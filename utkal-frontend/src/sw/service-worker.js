self.addEventListener("install", (evt) => self.skipWaiting());
self.addEventListener("activate", (evt) => self.clients.claim());
self.addEventListener("fetch", (evt) => {
  if (evt.request.url.includes("/sync") || evt.request.url.includes("/api/")) {
    evt.respondWith(fetch(evt.request).catch(() => caches.match(evt.request)));
  } else {
    evt.respondWith(caches.match(evt.request).then((r) => r || fetch(evt.request)));
  }
});
