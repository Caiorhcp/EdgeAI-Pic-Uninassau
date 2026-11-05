// Service worker do S.A.P.O.: guarda o site, o modelo e o OCR para funcionar sem internet.
// Só a consulta ao Datajud (/api/*) depende de conexão.
const CACHE = "sapo-v1";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

  if (request.mode === "navigate") {
    // Página: rede primeiro (versão nova quando online), cache quando offline
    event.respondWith(
      fetch(request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
          return res;
        })
        .catch(() => caches.match(request).then((hit) => hit ?? caches.match("/"))),
    );
    return;
  }

  if (url.pathname.startsWith("/_next/static/")) {
    // Arquivos com hash no nome nunca mudam: cache primeiro
    event.respondWith(caches.match(request).then((hit) => hit ?? fetchAndCache(request)));
    return;
  }

  // Modelo, OCR, fontes: responde do cache e atualiza em segundo plano
  event.respondWith(
    caches.match(request).then((hit) => {
      const fresh = fetchAndCache(request).catch(() => hit);
      return hit ?? fresh;
    }),
  );
});

async function fetchAndCache(request) {
  const res = await fetch(request);
  if (res.ok) {
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(request, copy));
  }
  return res;
}
