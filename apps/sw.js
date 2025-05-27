const CACHE_VERSION = 'v1.0';
const CACHE_NAME = `gidana-static-cache-${CACHE_VERSION}`;

const FILE_TYPES_TO_CACHE = [
    'js',
    'css',
    'png',
    'jpg',
    'jpeg',
    'gif',
    'svg',
    'woff',
    'woff2',
    'ttf',
    'eot',
    'ico',
    'webp',
    'json',
    'xml'
];

const PATHS_TO_CACHE = [
    '/',
    '/static/',
    '/static/js/',
    '/static/css/',
    '/static/img/',
    '/static/fonts/',
    '/static/favicons/',
    '/static/feedbacks/',
    '/static/icons/',
    '/static/brands/',
    '/static/media/',

];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[ServiceWorker] Opened cache');
                return cache.addAll(PATHS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('[ServiceWorker] Removing old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;

    const requestUrl = new URL(event.request.url);
    
    if (requestUrl.origin !== location.origin) return;

    const shouldCache = PATHS_TO_CACHE.some(path => 
        requestUrl.pathname.startsWith(path)
    ) || FILE_TYPES_TO_CACHE.some(ext => 
        requestUrl.pathname.endsWith(`.${ext}`)
    );

    if (shouldCache) {
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    if (response) {
                        return response;
                    }

                    const fetchRequest = event.request.clone();

                    return fetch(fetchRequest).then(response => {
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    });
                })
        );
    } else {
        event.respondWith(fetch(event.request));
    }
});