<template>
  <div :dir="direction" class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-800">{{ L.devices.title }}</h1>
      <p class="text-sm text-slate-500 mt-1">{{ L.devices.subtitle }}</p>
    </header>

    <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg" role="alert">{{ errorMessage }}</div>

    <section class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
        <h2 class="text-lg font-semibold text-slate-800">{{ L.devices.camera }}</h2>
        <div class="rounded-xl overflow-hidden bg-slate-950 aspect-video flex items-center justify-center">
          <video ref="videoElement" autoplay muted playsinline class="w-full h-full object-cover" :class="{ hidden: !cameraRunning }"></video>
          <span v-if="!cameraRunning" class="text-slate-400 text-sm px-6 text-center">{{ cameraSupported ? L.devices.startCamera : L.devices.cameraUnsupported }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button v-if="!cameraRunning" type="button" class="gov-btn-primary" :disabled="!cameraSupported" @click="startCamera">{{ L.devices.startCamera }}</button>
          <button v-else type="button" class="gov-btn-secondary" @click="stopCamera">{{ L.devices.stopCamera }}</button>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded-lg p-3">
          <label for="barcode-result" class="block text-sm font-medium text-slate-700">{{ L.devices.barcodeResult }}</label>
          <input id="barcode-result" v-model="barcodeValue" class="gov-input mt-2" autocomplete="off" />
          <p class="text-xs text-slate-500 mt-2">{{ L.devices.keyboardScannerHelp }}</p>
          <p v-if="lastScan" class="text-xs text-emerald-700 mt-2">{{ L.devices.lastScan }}: {{ lastScan }}</p>
        </div>
      </article>

      <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
        <h2 class="text-lg font-semibold text-slate-800">{{ L.devices.ocr }}</h2>
        <input type="file" accept="image/*" class="block w-full text-sm text-slate-600" @change="selectImage" />
        <img v-if="imagePreview" :src="imagePreview" alt="OCR preview" class="max-h-48 max-w-full rounded-lg border border-slate-200 object-contain" />
        <button type="button" class="gov-btn-primary" :disabled="!selectedImage || ocrRunning" @click="runOcr">
          {{ ocrRunning ? `${L.devices.ocrProgress} (${ocrProgress}%)` : L.devices.runOcr }}
        </button>
        <textarea v-model="ocrText" rows="8" class="gov-input" :placeholder="L.devices.ocrResult" :aria-label="L.devices.ocrResult"></textarea>
      </article>

      <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
        <h2 class="text-lg font-semibold text-slate-800">{{ L.devices.nfc }}</h2>
        <p class="text-sm text-slate-500">{{ nfcSupported ? L.devices.nfcResult : L.devices.nfcUnsupported }}</p>
        <button type="button" class="gov-btn-primary" :disabled="!nfcSupported || nfcReading" @click="readCard">{{ L.devices.readNfc }}</button>
        <pre v-if="nfcData" class="bg-slate-950 text-emerald-300 text-xs p-4 rounded-lg overflow-auto" dir="ltr">{{ JSON.stringify(nfcData, null, 2) }}</pre>
      </article>

      <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
        <h2 class="text-lg font-semibold text-slate-800">{{ L.devices.printing }}</h2>
        <p class="text-sm text-slate-500">{{ L.devices.browserPrinting }}</p>
        <button type="button" class="gov-btn-primary" @click="printTest">{{ L.devices.printTest }}</button>
        <div class="border-t border-slate-200 pt-4">
          <h3 class="font-medium text-slate-700">{{ L.devices.bridge }}</h3>
          <p class="text-sm mt-1" :class="bridge.connected ? 'text-emerald-700' : 'text-slate-500'">{{ bridge.connected ? L.devices.bridgeConnected : L.devices.bridgeDisconnected }}</p>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { L, useLocale } from '../composables/useLocale'
import { checkLocalDeviceBridge, installKeyboardBarcodeScanner, isCameraSupported, isNfcSupported, printHtml, readNfc, recognizeText, startBarcodeCamera } from '../services/deviceService'

const { direction } = useLocale()
const videoElement = ref(null)
const cameraControls = ref(null)
const cameraRunning = ref(false)
const cameraSupported = isCameraSupported()
const nfcSupported = isNfcSupported()
const barcodeValue = ref('')
const lastScan = ref('')
const selectedImage = ref(null)
const imagePreview = ref('')
const ocrText = ref('')
const ocrProgress = ref(0)
const ocrRunning = ref(false)
const nfcReading = ref(false)
const nfcData = ref(null)
const bridge = ref({ connected: false })
const errorMessage = ref('')
let removeKeyboardScanner = null

const canUseDevices = computed(() => cameraSupported || nfcSupported)

async function startCamera() {
  errorMessage.value = ''
  try {
    cameraControls.value = startBarcodeCamera(videoElement.value, (value) => {
      barcodeValue.value = value
      lastScan.value = value
    }, () => {})
    cameraRunning.value = true
  } catch (error) {
    errorMessage.value = error.name === 'NotAllowedError' ? L.devices.permissionDenied : L.devices.genericError
  }
}

async function stopCamera() {
  await cameraControls.value?.stop?.()
  cameraControls.value = null
  cameraRunning.value = false
}

function selectImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  selectedImage.value = file
  imagePreview.value = URL.createObjectURL(file)
  ocrText.value = ''
  ocrProgress.value = 0
}

async function runOcr() {
  if (!selectedImage.value) return
  ocrRunning.value = true
  errorMessage.value = ''
  try {
    ocrText.value = await recognizeText(selectedImage.value, (progress) => { ocrProgress.value = progress })
  } catch {
    errorMessage.value = L.devices.genericError
  } finally {
    ocrRunning.value = false
  }
}

async function readCard() {
  nfcReading.value = true
  errorMessage.value = ''
  try {
    await readNfc((reading) => { nfcData.value = reading })
  } catch (error) {
    errorMessage.value = error.name === 'NotAllowedError' ? L.devices.permissionDenied : L.devices.nfcUnsupported
  } finally {
    nfcReading.value = false
  }
}

function printTest() {
  try {
    printHtml({
      title: L.devices.printing,
      body: `<h1>${L.devices.printTest}</h1><div class="field"><span class="label">${L.devices.bridge}:</span>${bridge.value.connected ? L.devices.bridgeConnected : L.devices.bridgeDisconnected}</div>`,
    })
  } catch {
    errorMessage.value = L.devices.genericError
  }
}

onMounted(async () => {
  removeKeyboardScanner = installKeyboardBarcodeScanner((value) => {
    barcodeValue.value = value
    lastScan.value = value
  })
  bridge.value = await checkLocalDeviceBridge()
})

onBeforeUnmount(async () => {
  removeKeyboardScanner?.()
  await stopCamera()
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
})
</script>
