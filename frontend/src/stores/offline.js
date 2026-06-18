const DB_NAME = 'receipt-delivery-offline';
const DB_VERSION = 1;

export function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('receipts')) {
        db.createObjectStore('receipts', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('pending-sync')) {
        db.createObjectStore('pending-sync', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

export async function saveReceiptOffline(receipt) {
  const db = await openOfflineDB();
  const tx = db.transaction('receipts', 'readwrite');
  const store = tx.objectStore('receipts');
  store.put(receipt);
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getReceiptOffline(id) {
  const db = await openOfflineDB();
  const tx = db.transaction('receipts', 'readonly');
  const store = tx.objectStore('receipts');
  return new Promise((resolve, reject) => {
    const request = store.get(id);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function savePendingSync(action) {
  const db = await openOfflineDB();
  const tx = db.transaction('pending-sync', 'readwrite');
  const store = tx.objectStore('pending-sync');
  store.add(action);
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getPendingSyncActions() {
  const db = await openOfflineDB();
  const tx = db.transaction('pending-sync', 'readonly');
  const store = tx.objectStore('pending-sync');
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function clearPendingSyncAction(id) {
  const db = await openOfflineDB();
  const tx = db.transaction('pending-sync', 'readwrite');
  const store = tx.objectStore('pending-sync');
  store.delete(id);
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
