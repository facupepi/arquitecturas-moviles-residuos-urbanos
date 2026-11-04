// Service Worker para PWA San Francisco Residuos (UTN FRSFCO)
const CACHE_NAME = 'sf-residuos-v4.8';

const PRECACHE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './estilos.css',
  './vendor/leaflet/leaflet.css',
  './vendor/leaflet/leaflet.js',
  './vendor/lucide.min.js',
  './fonts/quicksand-latin.woff2',
  './brand/municipalidad-blanco.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable.png',
  './icons/apple-touch-icon.png'
];

// Instalación: precachear recursos esenciales de la App Shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Precacheando App Shell...');
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[ServiceWorker] Advertencia al precachear algunos recursos:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación: limpiar cachés obsoletas
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log('[ServiceWorker] Eliminando caché antigua:', name);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Intercepción de peticiones: red primero para el documento (siempre la última
// versión) y caché primero para el resto de los recursos estáticos
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const esDocumento = event.request.mode === 'navigate' ||
    (event.request.headers.get('accept') || '').includes('text/html');

  if (esDocumento) {
    event.respondWith(
      fetch(event.request).then((resp) => {
        if (resp && resp.status === 200) {
          const copia = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('./index.html', copia));
        }
        return resp;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((resp) => {
        if (resp && resp.status === 200 && resp.type === 'basic') {
          const copia = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copia));
        }
        return resp;
      });
    })
  );
});

// Manejo de Notificaciones Push Web. Llegan desde Firebase Cloud Messaging con la app cerrada;
// el contenido viaja en `data` (titulo, cuerpo) y también se aceptan cargas simples
self.addEventListener('push', (event) => {
  let carga = {};
  if (event.data) {
    try { carga = event.data.json(); } catch (e) { carga = { cuerpo: event.data.text() }; }
  }
  const d = Object.assign({}, carga.notification, carga.data);
  const titulo = d.titulo || d.title || 'San Francisco Residuos';
  const opciones = {
    body: d.cuerpo || d.body || 'Nuevo aviso del servicio de recolección.',
    icon: './icons/icon-192.png',
    badge: './icons/icon-192.png',
    vibrate: [100, 50, 100],
    tag: d.tag || undefined,
    data: { llegada: Date.now() }
  };

  // Con la app a la vista el aviso ya aparece dentro de ella: no se duplica
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((ventanas) => {
      if (ventanas.some((v) => v.visibilityState === 'visible')) return;
      return self.registration.showNotification(titulo, opciones);
    })
  );
});

// Clic en la notificación del sistema
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'cerrar') return;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('index.html') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('./index.html');
      }
    })
  );
});

