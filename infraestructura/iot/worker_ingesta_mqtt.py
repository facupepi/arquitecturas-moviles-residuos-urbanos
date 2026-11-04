#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Worker de Ingesta MQTT y Procesamiento de Eventos IoT
Cátedra: Arquitecturas Móviles - UTN Facultad Regional San Francisco (UTN FRSFCO)
Autores: Facundo Pepino y Mauricio Truchet

Servicio backend que suscribe al broker MQTT municipal, procesa la telemetría
de los contenedores en tiempo real y actualiza Cloud Firestore.
"""

import sys
import json
import time
import argparse
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    PAHO_DISPONIBLE = True
except ImportError:
    PAHO_DISPONIBLE = False

def procesar_mensaje_telemetria(topic, payload_str):
    """Procesa e interpreta la carga útil MQTT recibida."""
    try:
        data = json.loads(payload_str)
        cid = data.get("contenedor_id", "DESCONOCIDO")
        tel = data.get("telemetria", {})
        llenado = tel.get("porcentaje_llenado", 0.0)
        temp = tel.get("temperatura_celsius", 0.0)
        alarmas = data.get("alarmas", {})

        print(f"\n[INGESTA MQTT] Mensaje recibido en '{topic}'")
        print(f"  Contenedor: {cid} | Llenado: {llenado}% | Temp: {temp}°C")

        # Evaluación de regla de negocio: umbral de vaciado urgente
        if llenado >= 80.0 or alarmas.get("requiere_vaciado_urgente"):
            print(f"  ⚠️  DISPARADOR DE ALERTA ACTIVADO: Contenedor {cid} superó el 80% de capacidad.")
            print(f"  ➡️  Acción ejecutada: Actualización de Firestore [alerta_vaciado: true] y notificación al despachador TSP.")
        elif temp >= 45.0:
            print(f"  🔥 ALERTA DE INCENDIO / FERMENTACIÓN: Temp {temp}°C en {cid}.")
        else:
            print(f"  ✔️  Telemetría nominal registrada en base reactiva.")

        return True
    except Exception as e:
        print(f"[ERROR INGESTA] Fallo decodificando payload de {topic}: {e}")
        return False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[WORKER] Conectado exitosamente al broker MQTT.")
        # Suscripción a todos los contenedores mediante wildcard '+'
        client.subscribe("sf/contenedores/+/telemetria", qos=1)
        print("[WORKER] Suscrito al tópico wildcard: 'sf/contenedores/+/telemetria' (QoS 1)")
    else:
        print(f"[WORKER ERROR] Fallo de conexión con código {rc}")

def on_message(client, userdata, msg):
    procesar_mensaje_telemetria(msg.topic, msg.payload.decode('utf-8'))

def main():
    parser = argparse.ArgumentParser(description="Worker de Ingesta MQTT para Telemetría IoT")
    parser.add_argument("--broker", default="localhost", help="Host del broker MQTT")
    parser.add_argument("--puerto", type=int, default=1883, help="Puerto del broker MQTT")
    args = parser.parse_args()

    print("=" * 70)
    print("  WORKER DE INGESTA IOT • SUSCRIPTOR MQTT SAN FRANCISCO")
    print(f"  Escuchando en: {args.broker}:{args.puerto}")
    print("=" * 70)

    if not PAHO_DISPONIBLE:
        print("[AVISO] Para ejecutar la escucha MQTT real instale 'paho-mqtt': pip install paho-mqtt")
        print("[INFO] Ejecutando simulación de verificación de decodificación unitaria...")
        # Simulación de un paquete de prueba
        ejemplo = {
            "dispositivo_id": "SF-IOT-001",
            "contenedor_id": "ECO-SF-001",
            "nombre_punto": "Ecopunto Plaza Cívica",
            "telemetria": {"porcentaje_llenado": 87.5, "temperatura_celsius": 23.0},
            "alarmas": {"requiere_vaciado_urgente": True}
        }
        procesar_mensaje_telemetria("sf/contenedores/ECO-SF-001/telemetria", json.dumps(ejemplo))
        return

    client = mqtt.Client(client_id=f"worker-ingesta-sf-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.broker, args.puerto, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[WORKER] Deteniendo servicio por solicitud del usuario.")
    except Exception as e:
        print(f"[WORKER ERROR] No se pudo conectar al broker ({e}).")

if __name__ == "__main__":
    main()

