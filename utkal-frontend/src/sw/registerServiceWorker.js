export function registerSW() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(console.error);
  }
}
