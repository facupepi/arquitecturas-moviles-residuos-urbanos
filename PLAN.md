# Plan Integral de Desarrollo
# Caso de Estudio: Web Mobile App Gestión de Residuos Urbanos
**Cátedra:** Arquitecturas Móviles — UTN Facultad Regional San Francisco (UTN FRSFCO)  
**Docente:** Ing. Juan Pablo Bono  
**Alumnos:** Facundo Pepino y Mauricio Truchet  
**Fecha:** Noviembre 2026  

---

## 1. Objetivos y Alcance

Desarrollar la solución integral para el **Sistema de Gestión de Residuos Vecinales para la Ciudad de San Francisco**, conforme a los requerimientos especificados en el enunciado oficial de la cátedra:

1. **Diseño de Arquitectura Cloud y Microservicios:** Frontend Web Mobile (PWA), Backend contenerizado con Docker, persistencia y eventos en Firebase (Firestore, Storage, FCM, Auth), API de geolocalización y servicios de escalado con Kubernetes (HPA + Ingress).
2. **Prototipo Funcional Completo:**
   - **Aplicación Ciudadana:** Registro de residuos categorizados, solicitud de recolección para residuos especiales (voluminosos y peligrosos), mapa interactivo con ecopuntos de San Francisco y horarios, recepción de notificaciones de campañas.
   - **Panel de Control de Autoridades:** Telemetría y monitoreo de puntos en tiempo real, planificación y asignación de rutas a cuadrillas, gestión de incidentes y reclamos.
   - **Aplicación del Personal de Recolección:** Visualización de rutas asignadas, escáner de códigos QR de contenedores/puntos limpios, confirmación de tareas con registro de peso/timestamp y reporte de incidentes en vía pública.
   - **Plataforma de Mapeo y Geolocalización:** Integración con mapas (Leaflet / OpenStreetMap) centrados en la Ciudad de San Francisco (Córdoba), georreferenciando puntos limpios, ecopuntos y trazado de rutas optimizadas.
3. **Infraestructura de Escalabilidad y Monitoreo:**
   - Manifiestos de Kubernetes (`Deployment`, `Service`, `Ingress`, `HPA`).
   - Esquema y configuración de monitoreo con Prometheus y Grafana (métricas clave: latencia p95, throughput, uso de CPU/memoria y escalado elástico).
   - Configuración de Firebase (`firestore.rules`, `firestore.indexes.json`, `firebase.json`).
4. **Documentación Técnica e Informe Académico:**
   - Informe formal con la estética, tipografía institucional y calidad visual de las entregas previas (TP2, TP3, TP4, TP5 y TP Sistema de Puntos).
   - Diagramas vectoriales de arquitectura y secuencia de alta definición generados por script en Python (`fitz` / PyMuPDF).
   - Exportación automatizada a documentos finales `.docx` y `.pdf` mediante automatización Word (`win32com.client`) y plantilla oficial UTN FRSFCO.

---

## 2. Fases de Ejecución

### Fase 1: Estructura del Proyecto y Definición de Datos
- Creación del repositorio local en `Modelo de Arquitectura Cloud/TP Gestion Residuos Urbanos`.
- Modelado de datos en Firestore (colecciones: `solicitudes_residuos`, `ecopuntos`, `rutas_cuadrillas`, `incidentes`, `notificaciones`, `metricas_reciclaje`).
- Definición de reglas de seguridad (`firestore.rules`) e índices compuestos (`firestore.indexes.json`).

### Fase 2: Prototipo Funcional Web Mobile App
- Construcción de la aplicación web móvil en `app/` con interfaz adaptativa mobile-first:
  - Selector intuitivo de rol activo (Ciudadano, Autoridad Municipal, Personal de Recolección).
  - Módulo Ciudadano: formulario de registro con categorías de residuos (plásticos, cartón, orgánicos, vidrio, metales), selector de residuos especiales (voluminosos: podas/escombros; peligrosos: pilas/baterías/químicos), historial y avisos.
  - Módulo Autoridades: tablero de indicadores clave (KPIs), mapa en vivo de San Francisco, generador de rutas por cuadrilla y consola de incidentes.
  - Módulo Recolector: visualización de hoja de ruta ordenada, escáner QR interactivo de contenedores con confirmación de descarga y reporte de contenedores rotos/desbordados.
  - Mapa interactivo con Leaflet y OpenStreetMap centrado en San Francisco (Plaza Cívica, UTN FRSFCO, Parque Cincuentenario, Costanera, Ecopuntos de Av. Urquiza y Av. Cervantes).

### Fase 3: Especificación de Infraestructura Cloud, Docker y Kubernetes
- `Dockerfile` optimizado multi-stage para la API y la aplicación.
- Manifiestos de Kubernetes:
  - `deployment.yaml`: definición de réplicas, límites de CPU/memoria y probes (`livenessProbe`, `readinessProbe`).
  - `service.yaml`: exposición ClusterIP.
  - `ingress.yaml`: enrutamiento Ingress con terminación TLS.
  - `hpa.yaml`: HorizontalPodAutoscaler escalando de 2 a 10 réplicas al superar el 70% de consumo de CPU.
- Configuración de observabilidad:
  - `prometheus.yml`: scraping de métricas del cluster y de la aplicación.
  - `grafana-dashboard.json`: panel de monitoreo de disponibilidad, latencia y rendimiento de cuadrillas.

### Fase 4: Generación de Diagramas Vectoriales
- Creación de `diagramas.py` con PyMuPDF (`fitz`):
  - **Figura 1: Arquitectura General de la Solución** (Frontend Web Mobile PWA, API Gateway / Ingress, Microservicios K8s con HPA, Firebase Firestore en tiempo real, Storage, FCM y plataforma de monitoreo Prometheus/Grafana).
  - **Figura 2: Diagrama de Secuencia y Flujo de Trabajo** (Flujo integral: registro de residuo especial por el vecino, notificación en tiempo real al panel municipal, optimización y asignación de ruta a cuadrilla, navegación y escaneo QR en punto verde por el recolector, y cierre de tarea).

### Fase 5: Redacción de la Documentación Técnica
- Elaboración de `contenido.md` respetando las directivas académicas de UTN FRSFCO:
  - Títulos sin numerar en mayúsculas descriptivas.
  - Consigna literal destacada en cada sección.
  - Lenguaje técnico formal en tercera persona, oraciones concisas y viñetas estructuradas con etiqueta temática en negrita.
  - Justificación pormenorizada de Docker, Kubernetes, HPA, balanceo de carga y arquitectura de persistencia reactiva en Firebase.
  - Justificación de algoritmos de optimización de rutas (enfoque heurístico para el problema del viajante TSP).

### Fase 6: Compilación y Validación del Informe Final
- Implementación de `generar_informe.py` basado en la plantilla institucional del TP2/TP3.
- Actualización de tabla de contenidos automática de Word.
- Exportación a `PepinoFacundo_TruchetMauricio_GestionResiduos.docx` y `PepinoFacundo_TruchetMauricio_GestionResiduos.pdf`.
- Verificación de consistencia, estética, tablas y paginación.

