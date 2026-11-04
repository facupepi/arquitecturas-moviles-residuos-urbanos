# Caso de Estudio: Web Mobile App Gestión de Residuos Urbanos

Punto de entrada general. Quien examine este proyecto, persona o agente evaluador, debe leer este archivo primero.

---

## 1. Identificación Académica e Institucional

- **Institución:** Universidad Tecnológica Nacional — Facultad Regional San Francisco (UTN FRSFCO).
- **Carrera:** Ingeniería en Sistemas de Información.
- **Cátedra:** Arquitecturas Móviles (Ciclo Lectivo 2026).
- **Docente Titular:** Ing. Juan Pablo Bono.
- **Autores:** Facundo Pepino y Mauricio Truchet.
- **Tema:** Caso de Estudio — Gestión de Residuos Urbanos Vecinales para la Ciudad de San Francisco (Córdoba).

---

## 2. Dónde está cada componente

| Ruta relativa | Descripción y contenido |
|---|---|
| `PepinoFacundo_TruchetMauricio_GestionResiduos.docx` | Informe técnico entregable en formato Word (24 páginas, carátula e índice institucional de una sola página). |
| `PepinoFacundo_TruchetMauricio_GestionResiduos.pdf` | Versión final para evaluación en PDF (compilación vectorial, tipografía oficial, cero huecos). |
| `PLAN.md` | Plan integral de arquitectura, fases de ejecución y requerimientos de la consigna. |
| `app/` | Código fuente de la aplicación Web Mobile PWA (Leaflet, OpenStreetMap, TSP, escaneo QR y persistencia). |
| `app/index.html` | Aplicación interactiva con Pantalla de Ingreso/Login, roles RBAC (Ciudadano, Autoridad, Recolector), telemetría IoT, consola MQTT, GPS y Bottom Nav. |
| `app/manifest.json` | Manifiesto oficial PWA (A2HS, modo standalone, iconos 192/512 maskable, theme color `#0077ae`). |
| `app/sw.js` | Service Worker para funcionamiento Offline, cache-first de App Shell y receptor de Push Notifications. |
| `app/icons/` | Paquete de iconos oficiales en alta densidad (180x180, 192x192, 512x512 y maskable). |
| `app/package.json` | Manifiesto de dependencias y scripts de ejecución para Node.js y navegadores. |
| `infraestructura/Dockerfile` | Construcción contenerizada en múltiples etapas con servidor Nginx Alpine sin privilegios (UID 101, 29,7 MB). |
| `infraestructura/nginx.conf` | Servidor perimetral con cabeceras de seguridad OWASP, compresión gzip, CSP y endpoint `/healthz`. |
| `infraestructura/k8s/` | Manifiestos de Kubernetes (`deployment.yaml`, `service.yaml`, `ingress-hpa.yaml`, `iot-mosquitto.yaml`), `metrics-server-kind.yaml`, `probar_autoescalado.py` y la evidencia medida en `evidencia_autoescalado.txt`. |
| `infraestructura/notificaciones/enviar_push.py` | Emisor de notificaciones push por Firebase Cloud Messaging (a todos, por rol o vigilando campañas y cambios de solicitud). |
| `herramientas/` | Compilación de estilos (Tailwind) e íconos de la app y generador de los íconos PWA. |
| `pruebas/` | Pruebas automáticas contra la consigna, la nube, la geocerca, las reglas, el push y la carga. |
| `infraestructura/iot/` | Ecosistema IoT: `mosquitto.conf`, `simulador_sensor_mqtt.py` (sensores ultrasónicos) y `worker_ingesta_mqtt.py`. |
| `infraestructura/firestore.rules` | Reglas declarativas de seguridad y control de acceso basado en roles (RBAC) con esquemas estrictos. |
| `infraestructura/firestore.indexes.json` | Índices compuestos optimizados para consultas por estado, fecha y cuadrilla asignada. |
| `infraestructura/monitoreo/` | Observabilidad completa: `prometheus.yml`, reglas de alarma `alertas_residuos.yml` y tablero `grafana-dashboard.json`. |
| `informe-fuente/` | Código fuente de generación editorial: `contenido.md`, `generar_informe.py` y `diagramas.py`. |
| `informe-fuente/capturas/` | Capturas reales de la aplicación móvil en alta densidad (pantalla de ingreso, portal ciudadano, mapa, panel y recolector). |
| `informe-fuente/diagramas/` | Diagramas vectoriales de arquitectura integral con capa IoT (`fig1`) y secuencia completa de recolección (`fig2`). |

---

## 3. Características Técnicas Destacadas

1. **Autenticación Formal, Gestión de Sesiones y Reglas RBAC:**
   - **Pantalla de Ingreso Móvil:** Un solo botón, "Continuar con Google" (Firebase Auth). No hay ingreso por correo y contraseña, registro con formulario ni contraseñas en el código.
   - **Segregación Estricta de Aplicaciones por Rol (RBAC):** Cada rol (Vecino, Municipio, Cuadrilla) cuenta con una interfaz y navegación móvil dedicada e independiente. No existen conmutadores promiscuos de rol en la barra superior ni inferior; para alternar entre perfiles se requiere cerrar la sesión e ingresar con otra cuenta de Google.
   - **Experiencia de Usuario Limpia y Segura:** Las pantallas no muestran identificadores internos ni métricas de infraestructura.
   - **Sesiones Persistentes y Logout Seguro:** Sesión local con expiración de 7 días, avatar identificador y botón explícito de cierre de sesión.
   - **Quién es autoridad o cuadrilla:** lo decide el servidor, no la pantalla. El rol de cada cuenta de Google se guarda en la colección privada `roles_por_correo` de Firestore (nadie puede leerla ni escribirla desde la app; cada persona solo lee su propio documento) y las reglas de `infraestructura/firestore.rules` lo exigen. Se asigna con `python pruebas/asignar_rol.py correo@gmail.com autoridad` (o `recolector`, o `ninguno`); cualquier otra cuenta es vecino. Los correos no figuran en el repositorio.

2. **Capacidades Nativas Mobile & PWA Offline:**
   - **Web App Manifest & A2HS:** Instalable como aplicación nativa en la pantalla de inicio de Android y iOS sin intermediación de tiendas.
   - **Service Worker (`sw.js`):** Estrategia Cache-First que asegura operatividad plena en calle ante microcortes o falta de cobertura celular.
   - **Geolocalización GPS (`navigator.geolocation`):** Captura automática de coordenadas satelitales en solicitudes de vecinos y botón "Mi GPS" para centrar el mapa.
   - **Feedback Háptico (`navigator.vibrate`):** Respuesta táctil al escanear QR, confirmar pesaje, enviar solicitudes y recibir alertas de desborde.
   - **Web Notifications API:** Avisos push nativos del sistema operativo ante cambios de estado de trámites y alertas críticas ambientales.
   - **Barra de Navegación Inferior (Bottom Navigation Bar):** Ergonómica para manipulación táctil con una sola mano en pantallas móviles.

3. **Telemetría IoT en Tiempo Real con MQTT y WebSockets:**
   - **Broker Eclipse Mosquitto en Kubernetes:** Puerto 1883 TCP para ingesta de sensores y puerto 9001 WebSockets para streaming directo al panel municipal sin dependencias externas.
   - **Simulación de Sensores de Nivel:** Sensores ultrasónicos HC-SR04 / JSN-SR04T y sondas térmicas en los 5 contenedores de San Francisco con cálculo de porcentaje de llenado, temperatura y nivel de batería Li-Ion.
   - **Taxonomía de Tópicos:** `sf/contenedores/{id}/telemetria`, `sf/contenedores/{id}/alarmas` y `sf/contenedores/{id}/comandos` con calidad de servicio QoS 1 y Last Will and Testament (LWT).
   - **Auto-despacho por Umbral Crítico:** Cuando un contenedor supera el 80% de llenado, el worker de ingesta genera un incidente crítico de desborde y lo incluye de forma prioritaria en la matriz TSP de cuadrillas.

4. **Resolución del Problema del Viajante de Comercio (TSP):**
   - El despachador municipal agrupa las solicitudes pendientes y calcula la trayectoria óptima aplicando la distancia ortodrómica de Haversine y una heurística de vecino más cercano combinada con optimizaciones 2-opt.
   - En las mediciones del informe (sección 4) la mejora del 2-opt sobre el vecino más cercano fue de 5 a 7 % en distancia.

5. **Autenticación en Calle con Códigos QR y Geocerca:**
   - La aplicación de cuadrilla procesa códigos QR estandarizados (`sf-residuos://checkin?...`) con comprobación de geocerca en un radio máximo de 35 metros antes de habilitar el pesaje certificado.

6. **Cartografía Abierta y de Alta Resolución:**
   - Integración de Leaflet con el servicio de teselas cartográficas de alta definición Esri World Street Map y respaldo en OpenStreetMap Francia, sin claves de API.

---

## 4. Cómo Probar la Aplicación y la Autenticación

### Opción A: Ejecución Directa en el Navegador
1. Abrir el archivo `app/index.html` en cualquier navegador web moderno (Google Chrome, Mozilla Firefox o Microsoft Edge).
2. **Flujo de Ingreso y Autenticación:**
   - Sin sesión activa se muestra la pantalla de ingreso con "Continuar con Google".
   - El rol sale de la cuenta: con una de las cuentas de autoridad o cuadrilla (ver sección 3) se abre su panel; con cualquier otra, el portal del vecino.
   - El botón de salida (barra superior o modal de perfil) cierra la sesión y vuelve al ingreso.

3. **Prueba de los Módulos Operativos:**
   - **Rol Vecino:** Registrar residuos clasificados usando el botón "📍 Usar mi GPS", solicitar retiro especial y consultar el mapa de ecopuntos en San Francisco.
   - **Rol Municipio:** Visualizar las métricas y la **telemetría IoT en vivo** (tarjetas de contenedores con medidores de nivel, temperatura y batería, simulador interactivo MQTT y consola de tramas en vivo). Presionar "Calcular y Despachar Ruta Óptima" para ver el ruteo TSP.
   - **Rol Cuadrilla:** Abrir la hoja de ruta, presionar "Escanear Contenedor QR" (o "Probar Código Demo"), certificar el pesaje en kilogramos y reportar anomalías viales.

### Opción B: Ejecución con Servidor Local Node.js
```bash
cd app
npm start
# La aplicación abrirá automáticamente en http://localhost:8080
```

### Opción C: Ejecución del Ecosistema IoT y Simulación Cloud Firebase / MQTT
```bash
# 0. Aplicación Web PWA Desplegada en Producción:
# https://sf-residuos-urbanos-utn.web.app

# 1. Simulación telemática directa contra Google Cloud Firestore (sf-residuos-urbanos-utn):
python infraestructura/iot/simular_sensores_firebase.py --intervalo 4

# 2. Forzar un desborde crítico en el contenedor de Plaza Cívica contra Firebase:
python infraestructura/iot/simular_sensores_firebase.py --desborde

# 3. Simular la telemetría ultrasónica vía broker MQTT (Mosquitto K8s / TCP 1883):
python infraestructura/iot/simulador_sensor_mqtt.py --intervalo 3

# 4. Ejecutar el worker de ingesta desacoplado MQTT -> Firestore:
python infraestructura/iot/worker_ingesta_mqtt.py
```

### Opción D: Construcción y Ejecución con Docker
```bash
# Construir la imagen optimizada multi-stage
docker build -t sanfrancisco/gestion-residuos:latest -f infraestructura/Dockerfile .

# Ejecutar el contenedor en el puerto 8080
docker run -d -p 8080:8080 --name sf-residuos sanfrancisco/gestion-residuos:latest

# Comprobar la salud del servicio
curl http://localhost:8080/healthz
```

---

## 5. Compilación del Informe Técnico

El informe se redacta en `informe-fuente/contenido.md` y se compila automáticamente mediante automatización de Word (`win32com.client`) heredando la plantilla institucional de la cátedra:

```bash
cd informe-fuente
python generar_informe.py --salida "salida_revisada.docx" --sin-render
```

El script genera tanto el archivo `.docx` como el archivo `.pdf` con índice de contenidos de una sola página y verificación estricta de huecos y viudas.

## Cuentas y pruebas

- No hay contraseñas guardadas. Las pruebas automáticas crean cuentas temporales con clave aleatoria (`pruebas/ayuda_pruebas.py`), las usan y las borran al terminar; necesitan haber iniciado sesión en el CLI de Firebase (`firebase login`).
- Pruebas (cada una acepta una URL; sin ella usan la copia local de `app/`):
  - `python pruebas/test_consigna.py`: recorrido de cada rol contra la consigna.
  - `python pruebas/test_multidispositivo.py`: vecino, autoridad y cuadrilla sincronizados por la nube.
  - `python pruebas/test_geocerca.py`: geocerca de 35 m de la cuadrilla.
  - `python pruebas/test_reglas.py`: reglas de seguridad de Firestore con cuentas de cada rol y sin sesión.
  - `cd pruebas/reglas_emulador && npm install && npm test`: reglas de roles por correo de Google en el emulador (requiere JDK 21).
  - `python pruebas/test_estado_viejo.py`: el ingreso aparece aunque el navegador guarde datos viejos.
  - `python pruebas/prueba_carga.py URL CLIENTES SEGUNDOS`: carga concurrente.
- Las pruebas contra la nube eliminan los documentos que crean (marca `E2E-PRUEBA`).
- Los sensores simulados escriben en la nube con las credenciales de administración del CLI; sin sesión de autoridad, las reglas rechazan la escritura.

## Configuración de Firebase

La clave web del proyecto no se sube al repositorio: `app/firebase-config.js` está ignorado por git (copiá `app/firebase-config.ejemplo.js` y completalo con los datos de la consola de Firebase). La clave está restringida por sitio en Google Cloud. Ese archivo debe existir antes de `firebase deploy` y de construir la imagen Docker.

## Compilar los estilos e íconos

La app no usa CDN de estilos: `app/estilos.css` se genera con Tailwind y los íconos de `app/vendor/lucide.min.js` con solo los que se usan.

```bash
cd app && npm run estilos                      # regenera app/estilos.css
cd herramientas && npm install && python generar_iconos.py   # regenera app/vendor/lucide.min.js
```

Se repiten cada vez que se agregan clases o íconos nuevos en `app/index.html`.

## Notificaciones push

Los dispositivos que aceptan los avisos se registran solos (colección `dispositivos`). El emisor usa el CLI de Firebase (`firebase login`):

```bash
python infraestructura/notificaciones/enviar_push.py --titulo "Jornada de limpieza" --mensaje "Sábado 9 h en Plaza Cívica"
python infraestructura/notificaciones/enviar_push.py --vigilar   # avisa campañas nuevas y cambios de estado de solicitudes
```

## Autoescalado en un clúster local

`infraestructura/k8s/probar_autoescalado.py` documenta los pasos con kind y deja el registro en `evidencia_autoescalado.txt` (2 a 10 réplicas bajo carga).

## Guion de demostración (5 minutos)

1. **Vecino** (cuenta de Google cualquiera): abrir https://sf-residuos-urbanos-utn.web.app, ingresar, pedir un retiro de residuos voluminosos y mirar el mapa, los horarios y los contenedores.
2. **Autoridad** (otra ventana, cuenta de autoridad): ver llegar la solicitud en vivo, marcarla, elegir cuadrilla y despachar. El mapa dibuja la ruta por calles. Emitir una campaña.
3. **Cuadrilla** (tercera ventana, cuenta de cuadrilla): ver la parada asignada y la ruta, ingresar el código del contenedor, confirmar el pesaje y reportar un incidente.
4. **Push**: aceptar los avisos en el celular, cerrar la app y ejecutar `enviar_push.py`.
5. **Infraestructura**: mostrar `evidencia_autoescalado.txt`, el Dockerfile y el informe.

## Diseño

La interfaz sigue el diseño del TP5 (San Francisco Conecta): tipografía Quicksand, azul municipal, colores por servicio, menú lateral en escritorio y barra inferior en celulares. La paleta y las medidas están en la configuración de Tailwind al inicio de `app/index.html`.
