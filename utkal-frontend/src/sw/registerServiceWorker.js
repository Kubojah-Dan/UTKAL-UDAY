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

export function registerSW() {
  if (!("serviceWorker" in navigator)) return;

  if (import.meta.env.DEV) {
    disableServiceWorkersInDev();
    return;
  }

  navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(console.error);
}
