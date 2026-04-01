const CACHE_NAME = "utkal-uday-v3";
const STATIC_ASSETS = ["/", "/index.html", "/manifest.json", "/utkal-uday-logo.svg"];

// API routes that should be cached for offline fallback
const API_CACHE_PATTERNS = [
  "/questions",
  "/recommend",
  "/student/streak",
  "/student/daily-challenge",
  "/leaderboard",
  "/bkt/latest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)).catch(() => null)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  const isApiRoute = API_CACHE_PATTERNS.some((p) => url.pathname.includes(p));
  const isMutatingApi = url.pathname.includes("/sync") || url.pathname.includes("/auth");

  // Mutating API calls: network only, no cache
  if (isMutatingApi) {
    event.respondWith(fetch(event.request).catch(() => new Response("{}", { status: 503 })));
    return;
  }

  // API GET routes: network first, cache fallback
  if (isApiRoute) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)).catch(() => null);
          }
          return response;
        })
        .catch(() => caches.match(event.request).then((cached) => cached || new Response("{}", { status: 503 })))
    );
    return;
  }

  // Static assets: cache first, network fallback
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)).catch(() => null);
          }
          return response;
        })
        .catch(() => caches.match("/index.html"));
    })
  );
});
