self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('hangarin-cache-v1').then(function(cache) {
      return cache.addAll([
        '/',
        // Add your actual static CSS/JS files here to cache them
        // '/static/css/style.css',
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