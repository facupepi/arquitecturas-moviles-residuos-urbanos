#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de autoescalado del HPA en un clúster local (kind). Genera carga contra el servicio y registra
cada 10 s las réplicas y el consumo de CPU hasta que el HPA estabiliza. Deja la evidencia en
evidencia_autoescalado.txt.

Preparación (una vez):
  docker build -t ghcr.io/utn-frsfco/gestion-residuos-sf:1.0.0 -f infraestructura/Dockerfile .
  kind create cluster --name residuos
  kind load docker-image ghcr.io/utn-frsfco/gestion-residuos-sf:1.0.0 --name residuos
  kubectl create namespace produccion-residuos
  kubectl apply -f metrics-server-kind.yaml -f deployment.yaml -f service.yaml -f ingress-hpa.yaml
Uso: python probar_autoescalado.py [segundos_de_carga]
"""
import pathlib, subprocess, sys, time
from datetime import datetime

NS = "produccion-residuos"
SEGUNDOS = int(sys.argv[1]) if len(sys.argv) > 1 else 240
SALIDA = pathlib.Path(__file__).resolve().parent / "evidencia_autoescalado.txt"
CARGA = f"""apiVersion: apps/v1
kind: Deployment
metadata: {{name: generador-carga, namespace: {NS}}}
spec:
  replicas: 6
  selector: {{matchLabels: {{app: generador-carga}}}}
  template:
    metadata: {{labels: {{app: generador-carga}}}}
    spec:
      containers:
        - name: carga
          image: busybox:1.36
          command: ["sh", "-c", "for i in 1 2 3 4; do (while true; do wget -q -O /dev/null http://gestion-residuos-svc/; done) & done; wait"]
"""


def kubectl(*args, entrada=None):
    return subprocess.run(["kubectl", *args], input=entrada, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def instante():
    hpa = kubectl("-n", NS, "get", "hpa", "gestion-residuos-hpa", "-o",
                  "jsonpath={.status.currentReplicas}/{.status.desiredReplicas} cpu={.status.currentMetrics[0].resource.current.averageUtilization}%")
    listos = kubectl("-n", NS, "get", "deployment", "gestion-residuos-web", "-o", "jsonpath={.status.readyReplicas}")
    return f"{datetime.now():%H:%M:%S}  réplicas actuales/deseadas {hpa}  listas={listos or 0}"


def main():
    lineas = [f"Prueba de autoescalado — {datetime.now():%d/%m/%Y %H:%M}",
              kubectl("version", "--short") or "", "HPA: min 2, max 10, CPU 70 %, memoria 80 %", ""]
    def anotar(t):
        print(t, flush=True); lineas.append(t)
    anotar("== Estado inicial"); anotar(instante())
    kubectl("apply", "-f", "-", entrada=CARGA)
    anotar(f"== Carga aplicada (6 generadores × 4 bucles) durante {SEGUNDOS} s")
    fin = time.time() + SEGUNDOS
    while time.time() < fin:
        time.sleep(10); anotar(instante())
    kubectl("-n", NS, "delete", "deployment", "generador-carga")
    anotar("== Carga retirada (el HPA espera 300 s antes de reducir réplicas)")
    for _ in range(6):
        time.sleep(10); anotar(instante())
    anotar(""); anotar(kubectl("-n", NS, "describe", "hpa", "gestion-residuos-hpa").split("Events:")[-1].strip())
    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
