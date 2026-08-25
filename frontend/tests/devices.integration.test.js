import { afterEach, describe, expect, it, vi } from 'vitest'
import { installKeyboardBarcodeScanner, isCameraSupported, isNfcSupported, printHtml } from '../src/services/deviceService'

describe('device integration', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('captures keyboard-wedge barcode scans terminated by Enter', () => {
    const scans = []
    const remove = installKeyboardBarcodeScanner((value) => scans.push(value), { timeout: 200 })
    for (const key of ['9', '7', '8', '4']) window.dispatchEvent(new KeyboardEvent('keydown', { key }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    remove()
    expect(scans).toEqual(['9784'])
  })

  it('ignores short keyboard input and stops listening after cleanup', () => {
    const scans = []
    const remove = installKeyboardBarcodeScanner((value) => scans.push(value), { timeout: 200 })
    for (const key of ['1', '2']) window.dispatchEvent(new KeyboardEvent('keydown', { key }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    remove()
    for (const key of ['3', '4', '5']) window.dispatchEvent(new KeyboardEvent('keydown', { key }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    expect(scans).toEqual([])
  })

  it('detects browser capabilities without throwing', () => {
    expect(typeof isCameraSupported()).toBe('boolean')
    expect(typeof isNfcSupported()).toBe('boolean')
  })

  it('opens a printable transaction window', () => {
    const print = vi.fn()
    const printWindow = {
      document: { write: vi.fn(), close: vi.fn() },
      focus: vi.fn(),
      print,
    }
    vi.spyOn(window, 'open').mockReturnValue(printWindow)
    const result = printHtml({ title: 'Test', body: '<p>Transaction</p>' })
    expect(result).toBe(printWindow)
    expect(printWindow.document.write).toHaveBeenCalledWith(expect.stringContaining('<p>Transaction</p>'))
    expect(print).toHaveBeenCalled()
  })
})
