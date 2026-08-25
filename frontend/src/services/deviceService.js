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

export function printHtml({ title, body }) {
  const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700')
  if (!printWindow) throw new Error('Printing was blocked by the browser')
  printWindow.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>body{font-family:Arial,sans-serif;padding:32px;line-height:1.6}h1{color:#1f3a5f;border-bottom:2px solid #2563eb;padding-bottom:8px}.field{margin:8px 0}.label{font-weight:700;color:#475569;margin-inline-end:8px}@media print{button{display:none}}</style></head><body>${body}</body></html>`)
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
