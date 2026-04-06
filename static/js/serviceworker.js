self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open('hangarin-cache-v1').then(function(cache) {
            return cache.addAll([
                '/',
                '/static/tasks/theme.css',
                '/static/tasks/material-admin.css',
            ]);
        })
    );
});

self.addEventListener('fetch', function(e) {
    e.respondWith(
        caches.match(e.request).then(function(response) {
            return response || fetch(e.request);
        })
    );
});
