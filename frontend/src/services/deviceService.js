import { BrowserMultiFormatReader } from '@zxing/browser'

export function isCameraSupported() {
  return typeof navigator !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia)
}

export function isNfcSupported() {
  return typeof window !== 'undefined' && 'NDEFReader' in window
}

export function startBarcodeCamera(videoElement, onResult, onError = () => {}) {
  if (!isCameraSupported()) {
    throw new Error('Camera access is not supported by this browser')
  }
  const reader = new BrowserMultiFormatReader()
  let stopped = false
  const controlsPromise = reader.decodeFromConstraints(
    { video: { facingMode: { ideal: 'environment' } } },
    videoElement,
    (result, error) => {
      if (stopped) return
      if (result) onResult(result.getText(), result)
      else if (error && error.name !== 'NotFoundException') onError(error)
    },
  )
  return {
    async stop() {
      stopped = true
      const controls = await controlsPromise
      controls?.stop?.()
      reader.reset()
    },
  }
}

export function installKeyboardBarcodeScanner(onScan, { timeout = 80 } = {}) {
  let buffer = ''
  let lastKeyAt = 0
  const handler = (event) => {
    const now = Date.now()
    if (now - lastKeyAt > timeout) buffer = ''
    lastKeyAt = now
    if (event.key === 'Enter') {
      if (buffer.length >= 3) onScan(buffer)
      buffer = ''
      return
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
      buffer += event.key
    }
  }
  window.addEventListener('keydown', handler)
  return () => window.removeEventListener('keydown', handler)
}

export async function recognizeText(image, onProgress = () => {}) {
  const { createWorker } = await import('tesseract.js')
  const worker = await createWorker('eng+ara', 1, {
    logger: (message) => {
      if (message.status === 'recognizing text') onProgress(Math.round((message.progress || 0) * 100))
    },
  })
  try {
    const { data } = await worker.recognize(image)
    return data.text.trim()
  } finally {
    await worker.terminate()
  }
}

export async function readNfc(onReading) {
  if (!isNfcSupported()) throw new Error('Web NFC is not supported by this browser')
  const reader = new window.NDEFReader()
  await reader.scan()
  reader.onreading = (event) => {
    const records = Array.from(event.message.records || []).map((record) => ({
      recordType: record.recordType,
      mediaType: record.mediaType || '',
      data: decodeNdefData(record.data),
    }))
    onReading({ serialNumber: event.serialNumber || '', records })
  }
  return reader
}

function decodeNdefData(data) {
  if (!data) return ''
  try {
    return new TextDecoder().decode(data)
  } catch {
    return String(data)
  }
}

export function printHtml({ title, body, layout = 'a4' }) {
  const pageSizes = { a4: 'A4', a5: 'A5', 'a4-two-up': 'A4 landscape' }
  const pageSize = pageSizes[layout] || pageSizes.a4
  const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700')
  if (!printWindow) throw new Error('Printing was blocked by the browser')
  printWindow.document.write(`<!doctype html><html dir="auto"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>\n    :root{color:#1e293b;background:#fff}*{box-sizing:border-box}body{font-family:"Segoe UI",Tahoma,Arial,sans-serif;padding:24px;line-height:1.6;direction:inherit} .receipt{max-width:980px;margin:0 auto;border:1px solid #cbd5e1;padding:24px;background:#fff}.receipt-dual{display:grid;grid-template-columns:1fr 1fr;gap:8mm;max-width:194mm;margin:0 auto}.receipt-copy{min-width:0}.copy-label{text-align:center;color:#1d4e89;font-weight:700;border-bottom:1px dashed #94a3b8;padding-bottom:6px;margin-bottom:10px}.receipt-header{text-align:center;border-bottom:3px solid #1d4e89;padding-bottom:14px;margin-bottom:18px}.receipt-header h1{color:#1d4e89;border:0;margin:0 0 6px;padding:0;font-size:24px}.receipt-no{font-size:14px;color:#475569}.meta-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 24px;border:1px solid #e2e8f0;padding:14px;margin-bottom:18px}.field{margin:4px 0;min-width:0;overflow-wrap:anywhere}.label{font-weight:700;color:#475569;margin-inline-end:8px}.notes{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px;margin-bottom:18px;overflow-wrap:anywhere}.receipt h2{font-size:18px;color:#1d4e89;border-bottom:1px solid #cbd5e1;padding-bottom:6px}.receipt table{width:100%;border-collapse:collapse;margin-top:10px;font-size:12px}.receipt th,.receipt td{border:1px solid #cbd5e1;padding:8px;text-align:center;overflow-wrap:anywhere}.receipt th{background:#1d4e89;color:#fff}.receipt tr:nth-child(even) td{background:#f8fafc}.signatures{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px;margin-top:56px;text-align:center;font-weight:600}.receipt-footer{margin-top:28px;color:#64748b;text-align:center;font-size:11px}@media(max-width:640px){body{padding:8px}.receipt{padding:12px}.receipt-dual{display:block}.receipt-dual .receipt{margin-bottom:16px}.meta-grid{grid-template-columns:1fr}.receipt table{font-size:10px}.receipt th,.receipt td{padding:5px}.signatures{grid-template-columns:1fr;gap:24px}}@media print{body{padding:0}.receipt{border:0;max-width:none}.no-print,button{display:none!important}@page{size:${pageSize};margin:12mm}.receipt-dual{gap:5mm}.receipt-dual .receipt{padding:10mm}.receipt-dual .receipt table{font-size:9px}.receipt-dual .receipt th,.receipt-dual .receipt td{padding:4px}}\n    </style></head><body>${body}</body></html>`)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
  return printWindow
}

export async function checkLocalDeviceBridge(baseUrl = 'http://127.0.0.1:17321') {
  try {
    const response = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(1200) })
    if (!response.ok) throw new Error('Bridge unavailable')
    return { connected: true, ...(await response.json()) }
  } catch {
    return { connected: false }
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character])
}
