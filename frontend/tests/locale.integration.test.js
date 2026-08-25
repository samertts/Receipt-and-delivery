import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { L, currentLocale, setLocale } from '../src/composables/useLocale'

describe('locale integration', () => {
  afterEach(() => setLocale('ar'))

  it('switches the dictionary and document direction between Arabic and English', async () => {
    setLocale('en')
    await nextTick()
    expect(currentLocale.value).toBe('en')
    expect(L.nav.dashboard).toBe('Dashboard')
    expect(document.documentElement.lang).toBe('en')
    expect(document.documentElement.dir).toBe('ltr')

    setLocale('ar')
    await nextTick()
    expect(L.nav.dashboard).toBe('لوحة التحكم')
    expect(document.documentElement.lang).toBe('ar')
    expect(document.documentElement.dir).toBe('rtl')
  })
})
