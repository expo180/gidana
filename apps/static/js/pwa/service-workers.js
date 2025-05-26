const CACHE_NAME = 'gidana-cache-v1';
const ASSETS = [
  '/',
  '../../css/style.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png',
  '/static/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request)
      .then(response => response || fetch(e.request))
  );
});