#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simulador de Sensores IoT para Contenedores Urbanos Inteligentes
Cátedra: Arquitecturas Móviles - UTN Facultad Regional San Francisco (UTN FRSFCO)

Simula el comportamiento de nodos microcontroladores (ESP32 / LoRaWAN) equipados con:
- Sensor ultrasónico de distancia (HC-SR04 / JSN-SR04T) para calcular volumen ocupado.
- Sensor de temperatura (DS18B20 / DHT22) para prevención de fermentación o incendios.
- Monitor de batería Li-Ion 18650 (3.7V - 4.2V).
- Publicación periódica mediante protocolo MQTT hacia el broker municipal.
"""

import sys
import time
import json
import random
import argparse
from datetime import datetime

# Intentamos importar paho-mqtt; si no está instalado, se opera en modo mock de terminal
try:
    import paho.mqtt.client as mqtt
    PAHO_DISPONIBLE = True
except ImportError:
    PAHO_DISPONIBLE = False

# Lista de contenedores inteligentes de San Francisco equipados con telemetría IoT
CONTENEDORES_SF = [
    {
        "id": "ECO-SF-001",
        "sensor_id": "SF-IOT-001",
        "nombre": "Ecopunto Plaza Cívica",
        "ubicacion": "25 de Mayo y Libertador Norte",
        "altura_total_cm": 150.0,
        "coords": [-31.4280, -62.0825]
    },
    {
        "id": "ECO-SF-002",
        "sensor_id": "SF-IOT-002",
        "nombre": "Ecopunto Parque Cincuentenario",
        "ubicacion": "Urquiza y Los Piamonteses",
        "altura_total_cm": 180.0,
        "coords": [-31.4162, -62.0790]
    },
    {
        "id": "ECO-SF-003",
        "sensor_id": "SF-IOT-003",
        "nombre": "Ecopunto Costanera Norte",
        "ubicacion": "Cervantes y Caseros",
        "altura_total_cm": 150.0,
        "coords": [-31.4285, -62.1015]
    },
    {
        "id": "ECO-SF-004",
        "sensor_id": "SF-IOT-004",
        "nombre": "Punto Verde UTN FRSFCO",
        "ubicacion": "Av. de la Universidad 501",
        "altura_total_cm": 140.0,
        "coords": [-31.4421, -62.1054]
    },
    {
        "id": "ECO-SF-005",
        "sensor_id": "SF-IOT-005",
        "nombre": "Ecopunto Barrio Sarmiento",
        "ubicacion": "López y Planes 950",
        "altura_total_cm": 160.0,
        "coords": [-31.4390, -62.0850]
    }
]

def generar_telemetria(contenedor, simular_desborde=False):
    """Genera una lectura simulada de telemetría de sensor ultrasónico y ambientales."""
    h_tot = contenedor["altura_total_cm"]

    if simular_desborde:
        # Menor distancia al sensor = mayor llenado
        dist_sensor = random.uniform(5.0, 15.0)  # Muy cerca de la tapa
    else:
        dist_sensor = random.uniform(20.0, h_tot - 10.0)

    # Cálculo de llenado porcentual
    llenado_pct = max(0.0, min(100.0, ((h_tot - dist_sensor) / h_tot) * 100.0))
    temp_c = round(random.uniform(19.5, 27.5), 1)
    bateria_v = round(random.uniform(3.65, 4.15), 2)
    bateria_pct = round(((bateria_v - 3.3) / (4.2 - 3.3)) * 100)

    # Estado y banderas de alarma
    alerta_desborde = llenado_pct >= 80.0
    alerta_temperatura = temp_c >= 45.0

    payload = {
        "dispositivo_id": contenedor["sensor_id"],
        "contenedor_id": contenedor["id"],
        "nombre_punto": contenedor["nombre"],
        "coords": contenedor["coords"],
        "timestamp_unix": int(time.time()),
        "timestamp_iso": datetime.utcnow().isoformat() + "Z",
        "telemetria": {
            "distancia_sensor_cm": round(dist_sensor, 1),
            "altura_contenedor_cm": h_tot,
            "porcentaje_llenado": round(llenado_pct, 1),
            "temperatura_celsius": temp_c,
            "bateria_voltios": bateria_v,
            "bateria_porcentaje": max(0, min(100, bateria_pct)),
            "inclinacion_grados": round(random.uniform(0.1, 2.5), 1)
        },
        "alarmas": {
            "requiere_vaciado_urgente": alerta_desborde,
            "alerta_temperatura_alta": alerta_temperatura,
            "bateria_baja": bateria_pct < 20
        },
        "red": {
            "protocolo": "MQTT v5.0",
            "qos": 1,
            "rssi_dbm": random.randint(-85, -60)
        }
    }
    return payload

def main():
    parser = argparse.ArgumentParser(description="Simulador de Telemetría IoT vía MQTT - San Francisco Residuos")
    parser.add_argument("--broker", default="localhost", help="Dirección del broker MQTT (ej: localhost, broker.emqx.io)")
    parser.add_argument("--puerto", type=int, default=1883, help="Puerto del broker MQTT (defecto: 1883)")
    parser.add_argument("--intervalo", type=float, default=3.0, help="Segundos entre publicaciones")
    parser.add_argument("--iteraciones", type=int, default=10, help="Cantidad de paquetes a emitir (0 = infinito)")
    parser.add_argument("--forzar-desborde", action="store_true", help="Simula nivel crítico >85%% en Plaza Cívica")
    parser.add_argument("--cortar", action="store_true", help="Al terminar, corta la conexión sin despedirse (simula un sensor sin batería)")
    args = parser.parse_args()

    print("=" * 75)
    print("  SIMULADOR DE TELEMETRÍA IOT • PROTOCOLO MQTT - CIUDAD DE SAN FRANCISCO")
    print(f"  Broker destino: {args.broker}:{args.puerto}")
    print(f"  Intervalo: {args.intervalo}s | Iteraciones: {args.iteraciones}")
    print("=" * 75)

    cliente_mqtt = None
    conectado = False

    if PAHO_DISPONIBLE:
        try:
            id_cliente = f"simulador-sf-{random.randint(1000, 9999)}"
            cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=id_cliente)
            canal_estado = f"sf/sensores/{id_cliente}/estado"
            # Aviso de desconexión: si el sensor se queda sin batería o sin señal, el intermediario lo publica solo
            cliente_mqtt.will_set(canal_estado, json.dumps({"estado": "desconectado"}), qos=1, retain=True)

            def al_conectar(c, u, f, codigo, p=None):
                c.publish(canal_estado, json.dumps({"estado": "conectado"}), qos=1, retain=True)
                c.subscribe("sf/contenedores/+/comando", qos=1)

            def al_recibir_orden(c, u, msg):
                # Órdenes del municipio, por ejemplo {"intervalo": 10} para cambiar la frecuencia de muestreo
                try:
                    orden = json.loads(msg.payload.decode("utf-8"))
                    if "intervalo" in orden:
                        args.intervalo = max(0.5, float(orden["intervalo"]))
                        print(f"[ORDEN] Nueva frecuencia de muestreo: cada {args.intervalo} s")
                except ValueError:
                    pass

            cliente_mqtt.on_connect = al_conectar
            cliente_mqtt.on_message = al_recibir_orden
            cliente_mqtt.connect(args.broker, args.puerto, 60)
            cliente_mqtt.loop_start()
            conectado = True
            print(f"[MQTT] Conexión establecida exitosamente con {args.broker}:{args.puerto}")
        except Exception as e:
            print(f"[MQTT AVISO] No se pudo conectar con el broker ({e}). Operando en modo simulación local por consola.")
    else:
        print("[AVISO] Módulo 'paho-mqtt' no detectado. Operando en modo demostración local.")

    cuenta = 0
    try:
        while True:
            cuenta += 1
            # Seleccionamos un contenedor rotativo o aleatorio
            c = CONTENEDORES_SF[(cuenta - 1) % len(CONTENEDORES_SF)]
            
            # Si se solicita forzar desborde, lo aplicamos en el primer contenedor
            es_desborde = args.forzar_desborde and (c["id"] == "ECO-SF-001")
            data = generar_telemetria(c, simular_desborde=es_desborde)

            topic = f"sf/contenedores/{c['id']}/telemetria"
            payload_json = json.dumps(data, indent=2, ensure_ascii=False)
            payload_compacto = json.dumps(data, ensure_ascii=False)

            # Publicación MQTT
            if conectado and cliente_mqtt:
                cliente_mqtt.publish(topic, payload_compacto, qos=1)
                if data["alarmas"]["requiere_vaciado_urgente"]:
                    cliente_mqtt.publish(f"sf/contenedores/{c['id']}/alarma", json.dumps({
                        "motivo": "Llenado de 80 % o más", "porcentaje_llenado": data["telemetria"]["porcentaje_llenado"],
                        "timestamp_iso": data["timestamp_iso"]}), qos=1)

            # Salida en consola
            estado_alerta = "🚨 CRÍTICO (>80%)" if data["alarmas"]["requiere_vaciado_urgente"] else "🟢 NORMAL"
            print(f"\n[PAQUETE #{cuenta}] {datetime.now().strftime('%H:%M:%S')} • Tópico: '{topic}'")
            print(f"  Punto: {c['nombre']} ({c['id']}) • Sensor: {c['sensor_id']}")
            print(f"  Llenado: {data['telemetria']['porcentaje_llenado']}% [{estado_alerta}] | Temp: {data['telemetria']['temperatura_celsius']}°C | Batería: {data['telemetria']['bateria_porcentaje']}%")
            print(f"  Distancia medida: {data['telemetria']['distancia_sensor_cm']} cm / {data['telemetria']['altura_contenedor_cm']} cm")

            if args.iteraciones > 0 and cuenta >= args.iteraciones:
                print("\n[OK] Simulación de telemetría finalizada exitosamente.")
                break

            time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\n[INFO] Simulación interrumpida por el usuario.")
    finally:
        if conectado and cliente_mqtt:
            time.sleep(1)
            if args.cortar:
                cliente_mqtt.loop_stop()
                cliente_mqtt.socket().close()   # cierre abrupto: el intermediario publica el aviso de desconexión
            else:
                cliente_mqtt.publish(canal_estado, json.dumps({"estado": "apagado"}), qos=1, retain=True).wait_for_publish(3)
                cliente_mqtt.loop_stop()
                cliente_mqtt.disconnect()

if __name__ == "__main__":
    main()

