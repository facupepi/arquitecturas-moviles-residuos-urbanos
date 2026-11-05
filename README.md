# Caso de estudio: Gestión de Residuos Urbanos

Trabajo práctico de Arquitecturas Móviles (UTN Facultad Regional San Francisco, Ing. en Sistemas de Información, ciclo lectivo 2026). Docente: Ing. Juan Pablo Bono. Autores: Facundo Pepino y Mauricio Truchet.

- Aplicación publicada: https://sf-residuos-urbanos-utn.web.app
- Repositorio: https://github.com/facupepi/arquitecturas-moviles-residuos-urbanos
- Consigna: `Caso de Estudio - Gestion Residuos Urbanos.pdf`
- Informe: `PepinoFacundo_TruchetMauricio_GestionResiduos.pdf` (24 páginas) y su `.docx`

## Qué hace cada perfil

- Vecino: registra los residuos que separó (categoría y kilos), pide retiros de reciclables, voluminosos y peligrosos, consulta el mapa de ecopuntos, sus horarios y los de recolección por zona, y recibe las campañas.
- Autoridad: ve los contenedores y las solicitudes en tiempo real, arma rutas optimizadas por calles y las asigna a una cuadrilla, atiende incidentes y publica campañas.
- Cuadrilla: sigue su hoja de ruta, confirma cada parada con el código QR o el identificador (a menos de 35 metros del lugar), registra el peso y reporta problemas.

## Qué hay en cada carpeta

| Ruta | Contenido |
|---|---|
| `app/` | Aplicación web instalable: `index.html` (los tres perfiles), `sw.js` (funcionamiento sin conexión y avisos push), `manifest.json`, estilos compilados, fuentes, íconos, foto del ingreso y bibliotecas alojadas en `vendor/`. |
| `firebase.json` | Publicación en Firebase Hosting, con las cabeceras de seguridad, y ubicación de las reglas. |
| `infraestructura/firestore.rules` | Reglas de seguridad por perfil y validación de los datos que se escriben. |
| `infraestructura/Dockerfile` y `nginx.conf` | Imagen de una etapa sobre `nginx-unprivileged:alpine-slim`, sin privilegios (30,2 MB), con cabeceras de seguridad y `/healthz`. Medición en `evidencia_imagen.txt`. |
| `infraestructura/k8s/` | Despliegue, servicio, ingreso con límite por dirección y autoescalado de 2 a 10 réplicas; Mosquitto y el servicio de ingesta (`iot-mosquitto.yaml`). Evidencia en `evidencia_autoescalado.txt`. |
| `infraestructura/monitoreo/` | Prometheus, alertas, tablero de Grafana y `docker-compose.yml` para la prueba local. Evidencia de carga y alertas en `evidencia_carga.txt`. |
| `infraestructura/iot/` | Configuración de Mosquitto (`mosquitto.conf`, `acl`), simulador de sensores por MQTT, servicio de ingesta a Firestore y simulador que escribe directo en Firestore. Evidencia en `evidencia_mqtt.txt`. |
| `infraestructura/notificaciones/enviar_push.py` | Emisor de avisos push por Firebase Cloud Messaging. |
| `pruebas/` | Pruebas automáticas, mediciones y scripts de administración (ver abajo). |
| `informe-fuente/` | Fuente del informe (`contenido.md`), generador, diagramas y capturas. |
| `herramientas/` | Compilación de estilos (Tailwind) e íconos, y acceso a las credenciales del CLI de Firebase. |

## Perfiles y acceso

- Se ingresa solo con una cuenta de Google. La aplicación no maneja contraseñas.
- El rol lo decide el servidor: la colección privada `roles_por_correo` de Firestore indica qué cuentas son autoridad o cuadrilla, y cualquier otra entra como vecino. Se asigna con `python pruebas/asignar_rol.py correo@gmail.com autoridad` (o `recolector`, o `ninguno`). Los correos no figuran en el repositorio.
- Para cambiar de perfil se cierra la sesión y se ingresa con otra cuenta.

## Probar la aplicación en la computadora

Firebase Authentication no funciona abriendo el archivo directamente; hay que servirlo:

```bash
python -m http.server 8767 -d app      # http://localhost:8767/index.html
```

`app/firebase-config.js` no está en el repositorio: se copia de `app/firebase-config.ejemplo.js` con los datos de la consola de Firebase. La clave está restringida por sitio.

## Publicar una versión nueva

Cada vez que cambian los estilos hay que subir el número de versión en tres lugares: `estilos.css?v=` en `app/index.html`, el mismo nombre en la lista de `app/sw.js` y `CACHE_NAME` en `app/sw.js`. Sin eso, un navegador que ya tenía la app puede mezclar la página nueva con la hoja de estilos vieja.

```bash
cd app && npm run estilos && cd ..
firebase deploy --only firestore:rules,hosting
```

## Pruebas

Las pruebas crean cuentas temporales con clave aleatoria (`pruebas/ayuda_pruebas.py`), las usan y las borran; necesitan `firebase login`. Los documentos que crean llevan la marca `E2E-PRUEBA` y se eliminan al terminar, y las que vacían contenedores les devuelven su llenado. Las que usan la app aceptan una URL; sin ella sirven la copia local.

| Prueba | Qué verifica | Último resultado (5/11/2026, sitio publicado) |
|---|---|---|
| `test_consigna.py` | Recorrido de cada perfil contra la consigna | 43/43 |
| `test_reglas.py` | Reglas publicadas, con cuentas de cada perfil y sin sesión | 56/56 |
| `test_multidispositivo.py` | Vecino, autoridad y cuadrilla sincronizados por la nube | 18/18 |
| `test_push.py` | Aviso push con la aplicación cerrada | 6/6 |
| `test_geocerca.py` | Validación de la cuadrilla a 35 metros | 3/3 |
| `test_sin_conexion.py` | La aplicación abre sin red | 3/3 |
| `test_estado_viejo.py` | El ingreso aparece aunque el navegador guarde datos viejos | 3/3 |
| `reglas_emulador/test.cjs` | Reglas del repositorio en el emulador, incluidos los roles por correo | 43/43 |

Otras herramientas de `pruebas/`:

- `medir_rutas.py`: mejora del 2-opt sobre el vecino más cercano (`evidencia_rutas.txt`).
- `prueba_carga.py URL CLIENTES SEGUNDOS`: carga concurrente. Desde Windows conviene correrla dentro de la red de Docker (ver `infraestructura/monitoreo/evidencia_carga.txt`).
- `probar_google.py`: comprueba que el botón de Google abre la ventana de ingreso.
- `verificar_iconos.py`: comprueba que todos los íconos de cada perfil se dibujan.
- `admin_nube.py`: lectura y limpieza de datos con las credenciales del CLI (por ejemplo, devolver el llenado de un contenedor).

El emulador necesita JDK 21. Si `npm test` tarda demasiado en levantarlo, se puede iniciar el emulador aparte y correr `FIRESTORE_EMULATOR_HOST=127.0.0.1:8180 node test.cjs`.

## Sensores y MQTT

Canales: `sf/contenedores/{id}/telemetria` (mediciones), `sf/contenedores/{id}/alarma` (llenado de 80 % o más), `sf/contenedores/{id}/comando` (órdenes, por ejemplo `{"intervalo": 10}`) y `sf/sensores/{cliente}/estado`, donde el intermediario publica el aviso de desconexión si un sensor se corta. Todo con QoS 1.

Mosquitto solo acepta conexiones cifradas (puerto 8883) y con usuario; `infraestructura/iot/acl` limita qué canales usa cada uno (`sensores`, `ingesta`, `municipio`). Los certificados y el archivo de contraseñas se generan al desplegar y no se suben al repositorio:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout ca.key -out ca.crt -subj "/CN=CA residuos"
openssl req -newkey rsa:2048 -nodes -keyout servidor.key -out servidor.csr -subj "/CN=mosquitto-service"
printf "subjectAltName=DNS:localhost,DNS:mosquitto-service,IP:127.0.0.1\n" > san.ext
openssl x509 -req -in servidor.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -out servidor.crt -extfile san.ext
docker run --rm -v "$PWD:/c" eclipse-mosquitto:2.0.18-openssl mosquitto_passwd -b -c /c/passwd sensores <clave>   # repetir con -b para ingesta y municipio
```

Prueba en la computadora (con `passwd`, `acl` y `mosquitto.conf` en `config/`, y los certificados en `certs/`):

```bash
docker run -d -p 8883:8883 -v "$PWD/config:/mosquitto/config" -v "$PWD/certs:/mosquitto/certs:ro" eclipse-mosquitto:2.0.18-openssl
pip install paho-mqtt==2.1.0
MQTT_CA=certs/ca.crt MQTT_USUARIO=ingesta MQTT_CLAVE=<clave> python infraestructura/iot/worker_ingesta_mqtt.py
MQTT_CA=certs/ca.crt MQTT_USUARIO=sensores MQTT_CLAVE=<clave> python infraestructura/iot/simulador_sensor_mqtt.py --forzar-desborde
python infraestructura/iot/simular_sensores_firebase.py --intervalo 4      # alternativa sin MQTT
```

En la computadora, el servicio de ingesta escribe en Firestore con la sesión del CLI de Firebase (`firebase login`). En el clúster usa una cuenta de servicio cargada como secreto; los pasos están en el encabezado de `infraestructura/k8s/iot-mosquitto.yaml`.

## Docker, monitoreo y autoescalado

```bash
docker build -t sanfrancisco/gestion-residuos:latest -f infraestructura/Dockerfile .
docker compose -f infraestructura/monitoreo/docker-compose.yml up -d --build   # Grafana en :3300, Prometheus en :9190
```

`infraestructura/k8s/probar_autoescalado.py` documenta la prueba con kind (de 2 a 10 réplicas). La alerta de réplicas al máximo necesita kube-state-metrics en el clúster.

## Avisos push

```bash
python infraestructura/notificaciones/enviar_push.py --titulo "Jornada de limpieza" --mensaje "Sábado 9 h en Plaza Cívica"
python infraestructura/notificaciones/enviar_push.py --vigilar   # campañas nuevas, cambios de cada pedido y paradas nuevas de la cuadrilla
```

Con la aplicación abierta, los avisos llegan en vivo dentro de ella; con la aplicación cerrada, solo llegan si el emisor está enviándolos.

## Informe

```bash
cd informe-fuente
python tomar_capturas.py          # capturas de la app
python diagramas.py               # diagramas
python generar_informe.py         # .docx y .pdf (necesita Word); las direcciones web quedan como enlaces
```

## Límites conocidos

- Kubernetes, el autoescalado y Mosquitto se probaron en un clúster local (kind), no en un proveedor de nube.
- Con varias sesiones abiertas en la misma computadora hubo demoras aisladas de hasta 23 segundos en el tiempo real (`pruebas/evidencia_tiempo_real.txt`).
