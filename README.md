# starCAT web application

Run **starCAT** (*CellAnnoTator) on your own single-cell RNA-seq data directly in the browser:
https://immunogenomics.io/starcat/

starCAT annotates single-cell transcriptomes with curated catalogs of reference gene expression
programs (GEPs) and derives discrete annotations such as cell type, proliferation and activation
state. This site runs the published [`starcatpy`](https://pypi.org/project/starcatpy/) package
inside the browser with [Pyodide](https://pyodide.org) (Python compiled to WebAssembly), so data
never leaves the user's machine and there is no server-side compute.

## Using the site

1. Choose a reference catalog (see the [References](https://immunogenomics.io/starcat/references.html) page).
2. Select a counts file: an **H5AD** (AnnData) file or a **CellRanger H5** file
   (`filtered_feature_bc_matrix.h5`). Counts must be raw UMI counts with gene symbols as gene names.
3. Click **Run starCAT**. Results appear on the page with download links for
   `starcat_usage.tsv` (normalised program usage per cell) and `starcat_scores.tsv`
   (derived scores and labels), plus summary charts.

An example dataset (15,000 T cells, 55 MB) is linked from the page.

## How the site works

| File | Role |
|---|---|
| `starcat/index.html` | The page: form, progress, results and charts (Bootstrap + Vega-Lite). |
| `starcat/starcat-worker.js` | Web Worker that loads Pyodide, installs `anndata` and `starcatpy`, and runs the pipeline off the main thread so the page stays responsive. |
| `starcat/starcat_web.py` | The analysis pipeline, executed by Pyodide. |
| `starcat/references.html` | Table of available reference catalogs. |
| `starcat/references/` | Reference tarballs served to the browser (not in git; see below). |
| `download_references.py` | Downloads the reference tarballs listed in `current_references.tsv` into `starcat/references/`. |

`starcat_web.py` is a streaming version of `starcat.fit_transform()`. Rather than loading the
whole matrix with `anndata.read_h5ad`, it reads the HDF5 file in row blocks with `h5py`, keeps
only the genes present in the reference, accumulates per-gene scale factors in one pass and then
fits usages in batches of 10,000 cells with the package's own `refit_usage()`. Peak memory is
therefore set by the batch size rather than the dataset size, and results match the full-matrix
computation to ~1e-6. A 120,000-cell dataset runs in about 20 seconds.

Package versions are pinned in `starcat-worker.js`. `anndata` is pinned to 0.11 because newer
releases depend on `zarr`, which has no WebAssembly wheel; 0.11 reads files written by current
pandas/anndata releases.

The list of references shown in the dropdown is read from
[`current_references.tsv`](https://github.com/immunogenomics/starCAT/blob/main/src/starcat/current_references.tsv)
in the starCAT repository. When a reference is added there, run `download_references.py` on the
server so the tarball is available, and bump the `starcatpy` version in the worker if the package
was released with the new reference.

## Local development

```bash
python download_references.py          # once: fetch reference tarballs into starcat/references/
python -m http.server 8000 -d starcat   # then open http://localhost:8000
```

The page must be served over HTTP (not opened as a file) because it uses a Web Worker.

## Deployment

The live site is a checkout of this repository on the immunogenomics.io server, symlinked to
`/var/www/immunogenomics.io/public/starcat`. To deploy, merge to `main`, then on the server
`git pull` in that checkout and re-run `download_references.py` if references changed.

## Citation

If you use starCAT in your research, please cite:

> Kotliar D\*, Curtis M\*, Agnew R, et al. Reproducible single-cell annotation of programs
> underlying T-cell subsets, activation states and functions. *Nature Methods* 22, 1964–1980 (2025).
> https://doi.org/10.1038/s41592-025-02793-1

Please also cite the publication of the reference catalog you used.

## Related resources

- [starCAT Python package](https://github.com/immunogenomics/starCAT) (GitHub), [`starcatpy`](https://pypi.org/project/starcatpy/) on PyPI
- [Reference catalogs on Zenodo](https://zenodo.org/communities/starcat)
- [starCAT paper](https://www.nature.com/articles/s41592-025-02793-1)
