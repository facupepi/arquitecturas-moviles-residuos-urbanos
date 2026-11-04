# syntax=docker/dockerfile:1
# Contexto de build: raíz del TP. Uso: docker build -t sanfrancisco/gestion-residuos:latest -f infraestructura/Dockerfile .
# Dockerfile optimizado para producción - Web Mobile App Gestión de Residuos
FROM nginxinc/nginx-unprivileged:alpine-slim AS runner

LABEL maintainer="Facundo Pepino & Mauricio Truchet <utn-frsfco>"
LABEL description="Servicio Web Mobile App Gestión de Residuos Urbanos - San Francisco"

# Copia de configuración optimizada de Nginx con headers de seguridad heredables
COPY infraestructura/nginx.conf /etc/nginx/conf.d/default.conf

# Copia directa de la SPA autocontenida
COPY --chown=101:101 app/ /usr/share/nginx/html/

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --spider -q http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
