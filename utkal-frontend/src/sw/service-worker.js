self.addEventListener("install", (evt) => self.skipWaiting());
self.addEventListener("activate", (evt) => self.clients.claim());
self.addEventListener("fetch", (evt) => {
  const url = new URL(evt.request.url);
  const isApiRequest = url.origin !== self.location.origin || url.pathname.startsWith("/api/");

  if (isApiRequest || evt.request.url.includes("/sync")) {
    evt.respondWith(fetch(evt.request).catch(() => caches.match(evt.request)));
  } else {
    evt.respondWith(caches.match(evt.request).then((r) => r || fetch(evt.request)));
  }
});
