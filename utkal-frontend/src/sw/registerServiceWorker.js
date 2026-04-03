async function disableServiceWorkersInDev() {
  if (!("serviceWorker" in navigator)) return;

  try {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map((reg) => reg.unregister()));
  } catch (err) {
    console.warn("Failed to unregister service workers in dev", err);
  }

  if ("caches" in window) {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
    } catch (err) {
      console.warn("Failed to clear caches in dev", err);
    }
  }
}

async function cleanupLegacyServiceWorkers() {
  if (!("serviceWorker" in navigator)) return;

  try {
    const regs = await navigator.serviceWorker.getRegistrations();
    const legacyRegs = regs.filter((reg) =>
      [reg.active, reg.waiting, reg.installing]
        .map((worker) => worker?.scriptURL || "")
        .some((scriptUrl) => scriptUrl.includes("/service-worker.js"))
    );

    await Promise.all(legacyRegs.map((reg) => reg.unregister()));
  } catch (err) {
    console.warn("Failed to unregister legacy service workers", err);
  }

  if ("caches" in window) {
    try {
      const keys = await caches.keys();
      const legacyKeys = keys.filter((key) => key.startsWith("utkal-uday-v"));
      await Promise.all(legacyKeys.map((key) => caches.delete(key)));
    } catch (err) {
      console.warn("Failed to clear legacy caches", err);
    }
  }
}

export function registerSW() {
  if (!("serviceWorker" in navigator)) return;

  if (import.meta.env.DEV) {
    disableServiceWorkersInDev();
    return;
  }

  // Production service worker registration is handled by vite-plugin-pwa.
  cleanupLegacyServiceWorkers().catch(console.error);
}
