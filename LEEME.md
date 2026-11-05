# Caso de estudio: Gestión de Residuos Urbanos

Trabajo práctico de Arquitecturas Móviles (UTN Facultad Regional San Francisco, Ing. en Sistemas de Información, ciclo lectivo 2026). Docente: Ing. Juan Pablo Bono. Autores: Facundo Pepino y Mauricio Truchet.

Aplicación publicada: https://sf-residuos-urbanos-utn.web.app

## Qué hay en cada carpeta

| Ruta | Contenido |
|---|---|
| `PepinoFacundo_TruchetMauricio_GestionResiduos.pdf` y `.docx` | Informe técnico (24 páginas). |
| `app/` | Aplicación web instalable: `index.html` (los tres perfiles), `sw.js` (funcionamiento sin conexión y avisos push), `manifest.json`, estilos compilados, fuentes, íconos y bibliotecas alojadas en `vendor/`. |
| `infraestructura/firestore.rules` | Reglas de seguridad por perfil y validación de los datos que se escriben. |
| `infraestructura/Dockerfile` y `nginx.conf` | Imagen de una etapa sobre `nginx-unprivileged:alpine-slim`, sin privilegios (30,2 MB), con cabeceras de seguridad y `/healthz`. Medición en `evidencia_imagen.txt`. |
| `infraestructura/k8s/` | Despliegue, servicio, ingreso con límite por dirección y autoescalado de 2 a 10 réplicas; Mosquitto y el servicio de ingesta (`iot-mosquitto.yaml`). Evidencia del autoescalado en `evidencia_autoescalado.txt`. |
| `infraestructura/monitoreo/` | Prometheus (`prometheus.yml` para el clúster, `prometheus-local.yml` para la prueba local), alertas, tablero de Grafana y `docker-compose.yml`. Evidencia de carga y alertas en `evidencia_carga.txt`. |
| `infraestructura/iot/` | `mosquitto.conf`, simulador de sensores por MQTT, servicio de ingesta MQTT a Firestore y simulador que escribe directo en Firestore. Evidencia en `evidencia_mqtt.txt`. |
| `infraestructura/notificaciones/enviar_push.py` | Emisor de avisos push por Firebase Cloud Messaging. |
| `pruebas/` | Pruebas automáticas y mediciones (ver abajo). |
| `informe-fuente/` | Fuente del informe (`contenido.md`), generador, diagramas y capturas. |
| `herramientas/` | Compilación de estilos (Tailwind) y de los íconos. |

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

## Sensores y MQTT

Canales: `sf/contenedores/{id}/telemetria` (mediciones), `sf/contenedores/{id}/alarma` (llenado de 80 % o más), `sf/contenedores/{id}/comando` (órdenes, por ejemplo `{"intervalo": 10}`) y `sf/sensores/{cliente}/estado`, donde el intermediario publica el aviso de desconexión si un sensor se corta. Todo con QoS 1.

```bash
docker run -d -p 1883:1883 -v "$PWD/infraestructura/iot/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro" eclipse-mosquitto:2.0.18-openssl
pip install paho-mqtt==2.1.0
python infraestructura/iot/worker_ingesta_mqtt.py                                  # guarda cada lectura en Firestore
python infraestructura/iot/simulador_sensor_mqtt.py --intervalo 3 --forzar-desborde
python infraestructura/iot/simular_sensores_firebase.py --intervalo 4               # alternativa sin MQTT
```

En una computadora de desarrollo, el servicio de ingesta y el simulador directo escriben con la sesión del CLI de Firebase (`firebase login`). En el clúster, el servicio de ingesta usa una cuenta de servicio cargada como secreto (ver el encabezado de `iot-mosquitto.yaml`). Mosquitto acepta conexiones sin usuario: en producción hay que agregar usuarios y cifrado.

## Pruebas

Las pruebas crean cuentas temporales con clave aleatoria (`pruebas/ayuda_pruebas.py`), las usan y las borran; necesitan `firebase login`. Los documentos que crean llevan la marca `E2E-PRUEBA` y se eliminan al terminar. Las que usan la app aceptan una URL; sin ella sirven la copia local.

- `test_consigna.py`: recorrido de cada perfil contra la consigna.
- `test_multidispositivo.py`: vecino, autoridad y cuadrilla sincronizados por la nube.
- `test_geocerca.py`: validación de la cuadrilla a 35 metros.
- `test_reglas.py`: reglas publicadas, con cuentas de cada perfil y sin sesión.
- `reglas_emulador/test.cjs`: reglas del repositorio en el emulador, incluidos los roles por correo de Google (JDK 21; `npm install && npm test`).
- `test_estado_viejo.py`: el ingreso aparece aunque el navegador guarde datos viejos.
- `test_push.py`: aviso push con la aplicación cerrada.
- `medir_rutas.py`: mejora del 2-opt sobre el vecino más cercano (`evidencia_rutas.txt`).
- `prueba_carga.py URL CLIENTES SEGUNDOS`: carga concurrente. Desde Windows conviene correrla dentro de la red de Docker (ver `evidencia_carga.txt`).

## Docker, monitoreo y autoescalado

```bash
docker build -t sanfrancisco/gestion-residuos:latest -f infraestructura/Dockerfile .
docker compose -f infraestructura/monitoreo/docker-compose.yml up -d --build   # Grafana en :3300, Prometheus en :9190
```

`infraestructura/k8s/probar_autoescalado.py` documenta la prueba con kind. La alerta de réplicas al máximo necesita kube-state-metrics en el clúster.

## Avisos push

```bash
python infraestructura/notificaciones/enviar_push.py --titulo "Jornada de limpieza" --mensaje "Sábado 9 h en Plaza Cívica"
python infraestructura/notificaciones/enviar_push.py --vigilar   # envía las campañas nuevas y los cambios de estado de las solicitudes
```

Con la aplicación abierta, los avisos llegan en vivo dentro de ella; con la aplicación cerrada, solo llegan si el emisor está enviándolos.

## Informe

```bash
cd informe-fuente
python tomar_capturas.py          # capturas de la app
python diagramas.py               # diagramas
python generar_informe.py         # .docx y .pdf (necesita Word)
```
