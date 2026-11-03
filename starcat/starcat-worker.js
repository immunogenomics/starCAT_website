// Web Worker that hosts Pyodide so the page stays responsive while starCAT runs.
//
// Messages from the page:
//   {type: 'init', baseUrl}                       load Pyodide and the packages
//   {type: 'run', file, fileType, ref, refBase}   run starcat_web.py on a File
// Messages to the page:
//   {type: 'status', text}                        coarse setup/run stage
//   {type: 'progress', stage, fraction}           fraction in [0, 1], or -1 if unknown
//   {type: 'log', line, level}                    Python stdout/stderr
//   {type: 'ready'}                               packages installed
//   {type: 'result', result}                      output of starcat_web.py
//   {type: 'error', message, detail}

importScripts('https://cdn.jsdelivr.net/pyodide/v0.29.5/full/pyodide.js')

const STARCATPY_VERSION = '1.0.10'
// anndata 0.11 is the newest release that installs in Pyodide (0.12+ needs zarr, which has
// no WebAssembly wheel). Unlike 0.8 it reads files written by pandas 3 / anndata 0.12+.
const ANNDATA_SPEC = 'anndata>=0.11,<0.12'

const post = (type, data = {}) => self.postMessage({ type, ...data })

let pyodide = null
let pipelineCode = null
let busy = false

// starcat_web.py calls this (via `from js import report_progress`).
self.report_progress = (stage, fraction) => post('progress', { stage, fraction })

async function init(baseUrl) {
  post('status', { text: 'Loading Python runtime…' })
  pyodide = await loadPyodide({
    stdout: line => post('log', { line, level: 'info' }),
    stderr: line => post('log', { line, level: 'warn' }),
  })
  post('status', { text: 'Installing anndata…' })
  await pyodide.loadPackage('micropip')
  const micropip = pyodide.pyimport('micropip')
  await micropip.install(ANNDATA_SPEC)
  post('status', { text: 'Installing starcatpy…' })
  await micropip.install(['pyyaml', 'requests', 'scikit-learn'])
  // deps: false, otherwise starcatpy's unpinned anndata requirement pulls in 0.13
  await micropip.install.callKwargs(`starcatpy==${STARCATPY_VERSION}`, { deps: false })
  pyodide.runPython('import starcat')
  const resp = await fetch(new URL('starcat_web.py', baseUrl))
  if (!resp.ok) throw new Error(`Could not load starcat_web.py (HTTP ${resp.status})`)
  pipelineCode = await resp.text()
  post('ready')
}

// Expose the uploaded File to Python. Two options, neither touches the WebAssembly heap:
//  - MEMFS: one copy of the file in JS memory; h5py reads are plain memory reads (fast)
//  - WORKERFS: no copy, h5py reads go through synchronous Blob slices; ~6x slower in
//    practice because HDF5 issues many small reads, so only used for very large files
const WORKERFS_THRESHOLD = 1024 * 1024 * 1024

async function mountFile(file) {
  const workerfs = pyodide.FS.filesystems && pyodide.FS.filesystems.WORKERFS
  if (workerfs && file.size > WORKERFS_THRESHOLD) {
    const dir = '/mnt'
    try { pyodide.FS.mkdir(dir) } catch (e) { /* exists */ }
    pyodide.FS.mount(workerfs, { blobs: [{ name: 'data.h5', data: file }] }, dir)
    console.log('starcat-worker: large file, reading it in place via WORKERFS')
    return { path: `${dir}/data.h5`, cleanup: () => pyodide.FS.unmount(dir) }
  }
  const path = '/data.h5'
  pyodide.FS.writeFile(path, new Uint8Array(await file.arrayBuffer()))
  return { path, cleanup: () => pyodide.FS.unlink(path) }
}

async function run({ file, fileType, ref, refBase }) {
  if (busy) throw new Error('A run is already in progress')
  busy = true
  let cleanup = null
  try {
    post('status', { text: 'Opening file…' })
    const mounted = await mountFile(file)
    cleanup = mounted.cleanup
    pyodide.globals.set('DATA_PATH', mounted.path)
    pyodide.globals.set('FILE_TYPE', fileType)
    pyodide.globals.set('REF', ref)
    pyodide.globals.set('REF_BASE', refBase)
    post('status', { text: 'Running starCAT…' })
    const proxy = await pyodide.runPythonAsync(pipelineCode)
    const result = proxy.toJs({ dict_converter: Object.fromEntries })
    proxy.destroy()
    post('result', { result })
  } finally {
    busy = false
    if (cleanup) { try { cleanup() } catch (e) { /* ignore */ } }
  }
}

// Turn a Python traceback into a one-line headline plus the full detail.
function describeError(e) {
  const text = (e && e.message) || String(e)
  const lines = text.trim().split('\n')
  let headline = lines[lines.length - 1]
  const m = headline.match(/^\w+(?:\.\w+)*(?:Error|Exception|Warning):\s*(.*)$/)
  if (m) headline = m[1]
  return { message: headline, detail: text }
}

self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') await init(data.baseUrl)
    else if (data.type === 'run') await run(data)
  } catch (e) {
    console.error(e)
    post('error', describeError(e))
  }
}
