# starCAT Web Application

A privacy-preserving web application for running **starCAT** (star-CellAnnoTator) directly in your browser.

## Overview

starCAT annotates single-cell RNA-seq data with predefined gene expression programs and  infers derived discrete annotations such as cell type labels. This web implementation uses **Pyodide** (Python compiled to WebAssembly) to run the complete starCAT algorithm entirely in your browser.

## Key Features

- **Complete Privacy**: All computation happens client-side - your data never leaves your machine
- **No Installation Required**: Run sophisticated bioinformatics analysis directly in your browser
- **Multiple Input Formats**: Takes raw count data in both H5AD (AnnData) and MTX (Matrix Market) file formats
- **Curated Reference Catalogs**: Access to pre-built reference datasets for various tissues and species
- **Zero Infrastructure**: No backend servers or API limits

## Quick Start

1. **Visit the application** (https://immunogenomics.io/starcat)
2. **Select a reference catalog** from the dropdown menu
3. **Choose your file format** (H5AD or MTX)
4. **Upload your data**:
   - H5AD: Single `.h5ad` file (up to ~50,000 cells or 700MB)
   - MTX: Three files (matrix, features, barcodes)
5. **Click "Run starCAT"** and wait for processing
6. **Download results**: Two TSV files (usage scores and detailed scores) plus interactive visualizations

## Supported File Formats

### H5AD Format
Standard AnnData format for single-cell data stored in HDF5 files.

### CellRanger H5 Format
H5 format output by CellRanger (e.g. filtered_feature_bc_matrix.h5) for users who want to avoid H5Ad

## Reference Catalogs

Pre-built reference catalogs are available for the following:
- Human T cells across tissies and diseases (TCAT.V1)
- Human myeloid cells from gliomas (MYELOID.GLIOMA.V1)
- Human bone marrow derived CD34+ hematapoetic stem cells (BONEMARROW.CD34POS.HSPC.V1)

View the full catalog at the **References** page.

## Local Development

Since this is a static website, you can run it locally with any web server:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js http-server
npx http-server

# Or simply open starcat/index.html in your browser
```

## Citation

If you use starCAT in your research, please cite:

```
Kotliar, D.*, Curtis, M.*, Agnew, R. et al. Reproducible single-cell annotation of programs underlying T cell subsets, activation states and functions. Nat Methods 22, 1964–1980 (2025). https://doi.org/10.1038/s41592-025-02793-1
```

## Related Resources

- **GitHub** for [starCAT algorithm](https://github.com/immunogenomics/starCAT)
- **Reference Catalogs**: Available on [Zenodo](https://zenodo.org/communities/starcat/records?q=&l=list&p=1&s=10&sort=newest)
- **Documentation**: See [manuscript](https://www.nature.com/articles/s41592-025-02793-1#citeas) for methodology details
