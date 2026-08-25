# Device integration sources

- ZXing browser: https://github.com/zxing-js/browser — browser layer for ZXing barcode decoding; inspected via GitHub CLI on 2026-08-25. Reported 305 stars and pushed 2026-07-06.
- Tesseract.js: https://github.com/naptha/tesseract.js — JavaScript OCR supporting more than 100 languages; inspected via GitHub CLI on 2026-08-25. Reported 38,667 stars and pushed 2026-05-17.

Implementation decision: use ZXing browser for camera barcode scanning and Tesseract.js for client-side English/Arabic OCR. Use browser print for ordinary printers, Web NFC when supported, keyboard-wedge handling for USB barcode scanners, and an optional localhost bridge contract for devices that require OS-level access. Browser APIs require a secure origin and user permission; Web NFC is capability-detected and remains optional.
