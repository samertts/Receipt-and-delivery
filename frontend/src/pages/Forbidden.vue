<template>
  <div class="min-h-[60vh] flex items-center justify-center p-6" :dir="direction">
    <section class="max-w-md text-center bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
      <div class="mx-auto mb-4 w-14 h-14 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center text-2xl font-bold">!</div>
      <h1 class="text-2xl font-bold text-slate-800">{{ L.access.forbidden }}</h1>
      <p class="text-sm text-slate-500 mt-3">{{ L.access.forbiddenMessage }}</p>
      <router-link to="/dashboard" class="inline-flex mt-6 gov-btn-primary">{{ L.access.backToDashboard }}</router-link>
    </section>
  </div>
</template>

<script setup>
import { L, useLocale } from '../composables/useLocale'

const { direction } = useLocale()
</script>
