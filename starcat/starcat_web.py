"""
starCAT in the browser: a streaming, bounded-memory version of the starcatpy pipeline.

This file is fetched by index.html and executed with Pyodide (runPythonAsync).
It expects these globals to be set from JavaScript before it runs:

    DATA_PATH  path of the uploaded counts file inside the Pyodide filesystem
    FILE_TYPE  'h5ad' or '10x_h5'
    REF        name of the starCAT reference, e.g. 'TCAT.V1'
    REF_BASE   absolute URL of the directory holding <REF>.tar.gz

Why not just call starcat.fit_transform(anndata.read_h5ad(...))?  Browser memory is
scarce (a few GB of WebAssembly heap at most) and read_h5ad loads the full matrix
plus every obs/var column.  The references only use a few thousand genes and the
per-cell NNLS refit is independent across cells, so instead we:

  pass 1  stream the matrix in row blocks, keep only reference genes, and accumulate
          per-gene sums to reproduce sklearn.preprocessing.scale(with_mean=False)
  pass 2  stream again in batches of BATCH cells, scale, and refit usages with the
          same starcat.refit_usage() call the package uses

Peak memory is then set by the batch size, not the dataset size.  Results match
starcat.fit_transform on the full matrix to ~1e-6 (differences come only from the
random initialisation of the NMF solver).
"""

import gc
import os
import time
import warnings

import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp
import starcat
from anndata.io import read_elem
from pyodide.http import pyfetch

warnings.filterwarnings("ignore")

CHUNK = 2000     # rows per read in the scan pass
BATCH = 10000    # cells per NMF refit
MIN_OVERLAP = 0.2  # fraction of reference genes that must be present in the query

_warnings = []


def warn(msg):
    _warnings.append(msg)
    print("WARNING: " + msg)


def progress(stage, fraction=None):
    """Report progress to JavaScript if a callback was provided."""
    try:
        from js import report_progress
    except ImportError:
        return
    report_progress(stage, -1 if fraction is None else float(fraction))


def _decode(arr):
    return np.array([x.decode() if isinstance(x, bytes) else x for x in arr], dtype=object)


# ----------------------------------------------------------------------------
# Row-block readers: all yield cells x genes CSR blocks via .rows(i, j)
# ----------------------------------------------------------------------------

class CompressedRows:
    """Compressed-sparse rows stored in HDF5 (anndata csr_matrix, or CellRanger's
    genes x cells CSC, whose column pointer is exactly a cells x genes row pointer)."""

    def __init__(self, data, indices, indptr, n_rows, n_cols):
        self.data, self.indices, self.indptr = data, indices, indptr
        self.n_rows, self.n_cols = int(n_rows), int(n_cols)

    def rows(self, i, j):
        j = min(j, self.n_rows)
        a, b = int(self.indptr[i]), int(self.indptr[j])
        return sp.csr_matrix(
            (self.data[a:b], self.indices[a:b], self.indptr[i:j + 1] - a),
            shape=(j - i, self.n_cols),
        )


class DenseRows:
    def __init__(self, dataset):
        self.ds = dataset
        self.n_rows, self.n_cols = (int(x) for x in dataset.shape)

    def rows(self, i, j):
        return sp.csr_matrix(np.asarray(self.ds[i:j]))


class MemoryRows:
    def __init__(self, X):
        self.X = sp.csr_matrix(X)
        self.n_rows, self.n_cols = self.X.shape

    def rows(self, i, j):
        return self.X[i:j]


def open_matrix(f, path):
    g = f[path]
    if isinstance(g, h5py.Group):
        enc = g.attrs.get("encoding-type", "")
        shape = tuple(int(x) for x in g.attrs["shape"])
        if enc == "csr_matrix":
            return CompressedRows(g["data"], g["indices"], g["indptr"][:], *shape)
        if enc == "csc_matrix":
            warn(f"'{path}' is stored column-major (csc); loading it whole. "
                 "Saving the matrix as csr would use less memory.")
            X = sp.csc_matrix((g["data"][:], g["indices"][:], g["indptr"][:]), shape=shape)
            return MemoryRows(X)
        raise ValueError(f"Unsupported matrix encoding {enc!r} at '{path}'.")
    return DenseRows(g)


def looks_like_counts(rows):
    block = rows.rows(0, min(500, rows.n_rows))
    d = block.data
    return d.size == 0 or bool(np.all(d == np.floor(d)))


def open_h5ad(f):
    """Return (rows, gene names, cell names, description of the matrix used).

    Prefers the first integer-valued matrix among X, layers/counts and raw/X, so a
    file whose X was log-normalised but still carries raw counts just works.
    """
    candidates = ["X"]
    if "layers" in f and "counts" in f["layers"]:
        candidates.append("layers/counts")
    if "raw" in f and "X" in f["raw"]:
        candidates.append("raw/X")
    chosen = None
    for path in candidates:
        rows = open_matrix(f, path)
        if looks_like_counts(rows):
            chosen = (rows, path)
            break
    if chosen is None:
        rows, path = open_matrix(f, "X"), "X"
        warn("The matrix does not look like integer counts. starCAT expects raw counts; "
             "results on normalised data are not reliable.")
    else:
        rows, path = chosen
        if path != "X":
            print(f"X does not contain integer counts; using '{path}' instead.")
    var = f["raw/var"] if path.startswith("raw/") else f["var"]
    genes = pd.Index(read_elem(var).index.astype(str))
    cells = pd.Index(read_elem(f["obs"]).index.astype(str))
    if len(genes) != rows.n_cols or len(cells) != rows.n_rows:
        raise ValueError(f"'{path}' has shape {(rows.n_rows, rows.n_cols)} but the file "
                         f"has {len(cells)} cells and {len(genes)} genes.")
    return rows, genes, cells, path


def open_10x(f):
    """CellRanger H5 (v3 'matrix' group, or v2 genome group)."""
    if "matrix" in f:
        g = f["matrix"]
        names = _decode(g["features/name"][:])
        if "features/feature_type" in g:
            ftype = _decode(g["features/feature_type"][:])
            not_gex = ftype != "Gene Expression"
            if not_gex.any():
                print(f"Ignoring {int(not_gex.sum())} non-gene features "
                      f"({', '.join(sorted(set(ftype[not_gex])))}).")
                names = names.copy()
                names[not_gex] = ""
    else:  # CellRanger v2: one group per genome
        g = f[list(f.keys())[0]]
        names = _decode(g["gene_names"][:])
    n_genes, n_cells = (int(x) for x in g["shape"][:])
    rows = CompressedRows(g["data"], g["indices"], g["indptr"][:], n_cells, n_genes)
    return rows, pd.Index(names.astype(str)), pd.Index(_decode(g["barcodes"][:]).astype(str)), "matrix"


# ----------------------------------------------------------------------------
# Reference
# ----------------------------------------------------------------------------

async def load_reference(ref, base_url, cachedir="/refs"):
    if not os.path.isdir(os.path.join(cachedir, ref)):
        progress("Downloading reference " + ref)
        resp = await pyfetch(f"{base_url}{ref}.tar.gz")
        if not resp.ok:
            raise RuntimeError(f"Reference '{ref}' is not available on this server "
                               f"(HTTP {resp.status} for {base_url}{ref}.tar.gz).")
        await resp.unpack_archive(extract_dir=cachedir)
    try:
        return starcat.starCAT(reference=ref, cachedir=cachedir)
    except Exception as e:
        if "not found in list of pre-built reference names" in str(e):
            raise RuntimeError(f"Reference '{ref}' is not known to the installed starcatpy "
                               "version; the site needs a starcatpy upgrade.") from e
        raise


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------

async def run(data_path, file_type, ref, ref_base):
    t_start = time.time()
    cat = await load_reference(ref, ref_base)
    ref_genes = cat.ref.columns

    with h5py.File(data_path, "r") as f:
        progress("Reading file")
        if file_type == "10x_h5":
            rows, genes, cells, matrix_used = open_10x(f)
        else:
            rows, genes, cells, matrix_used = open_h5ad(f)
        n = rows.n_rows
        if n == 0:
            raise ValueError("The file contains no cells.")
        print(f"{n:,} cells x {rows.n_cols:,} genes in '{matrix_used}'")

        dup = genes.duplicated(keep="first") & (genes != "")
        if dup.any():
            warn(f"{int(dup.sum())} duplicate gene names; keeping the first occurrence of each.")
        keep = np.where(genes.isin(ref_genes) & ~dup)[0]
        n_ref = len(ref_genes)
        print(f"{len(keep)} out of {n_ref} genes in the reference overlap with the query")
        if len(keep) < MIN_OVERLAP * n_ref:
            raise ValueError(
                f"Only {len(keep)} of the {n_ref} reference genes were found in the query. "
                "starCAT references use HGNC gene symbols (e.g. CD3E, GZMB) as gene names; "
                "if your file uses Ensembl IDs or another species, rename the genes first.")
        overlap = genes[keep]
        spectra = cat.ref[overlap].values.astype(np.float32)

        # pass 1: integer/negativity checks and per-gene variance (ddof=0, as sklearn.scale)
        s1 = np.zeros(len(keep))
        s2 = np.zeros(len(keep))
        non_integer = negative = False
        for i in range(0, n, CHUNK):
            progress("Scanning genes", i / n)
            c = rows.rows(i, i + CHUNK)[:, keep]
            d = c.data.astype(np.float64)
            if not non_integer and (d != np.floor(d)).any():
                non_integer = True
            if not negative and (d < 0).any():
                negative = True
            s1 += np.asarray(c.sum(axis=0, dtype=np.float64)).ravel()
            s2 += np.asarray(sp.csr_matrix((d * d, c.indices, c.indptr), shape=c.shape)
                             .sum(axis=0, dtype=np.float64)).ravel()
        if negative:
            raise ValueError("The count matrix contains negative values; starCAT needs raw counts.")
        if non_integer and not any("integer counts" in w for w in _warnings):
            warn("The matrix is not integer-valued; starCAT expects raw counts.")
        zero_genes = int((s1 == 0).sum())
        if zero_genes:
            warn(f"{zero_genes} reference genes have zero counts in the query.")
        mean = s1 / n
        scale = np.sqrt(np.maximum(s2 / n - mean ** 2, 0))
        scale[scale == 0] = 1.0
        inv_scale = (1.0 / scale).astype(np.float32)

        # pass 2: scale and refit usages batch by batch
        parts = []
        for i in range(0, n, BATCH):
            progress("Fitting usages", i / n)
            c = rows.rows(i, i + BATCH)[:, keep].astype(np.float32)
            c.data *= inv_scale[c.indices]
            parts.append(cat.refit_usage(c, spectra, cat._nmf_kwargs.copy()))
            del c
            gc.collect()

    progress("Computing scores")
    usage = pd.DataFrame(np.vstack(parts), index=cells, columns=cat.ref.index)
    del parts
    cat.overlap_genes = list(overlap)
    cat.usage = usage
    cat.usage_norm = usage.div(usage.sum(axis=1), axis=0)
    cat.scores = cat.compute_addon_scores() if cat.score_data is not None else None

    result = {
        "usage_tsv": cat.usage_norm.to_csv(sep="\t"),
        "scores_tsv": None if cat.scores is None else cat.scores.to_csv(sep="\t"),
        "n_cells": int(n),
        "n_genes_overlap": int(len(keep)),
        "n_genes_reference": int(n_ref),
        "matrix_used": matrix_used,
        "warnings": list(_warnings),
        "seconds": round(time.time() - t_start, 1),
    }
    print(f"starCAT completed in {result['seconds']} s")
    gc.collect()
    return result


_warnings.clear()
await run(DATA_PATH, FILE_TYPE, REF, REF_BASE)  # noqa: F821 (globals set from JavaScript)
