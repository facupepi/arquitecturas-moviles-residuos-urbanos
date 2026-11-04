#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simulador de Sensores IoT para Contenedores Urbanos con Conexión Cloud Firestore
Cátedra: Arquitecturas Móviles - UTN Facultad Regional San Francisco (UTN FRSFCO)
Autores: Facundo Pepino y Mauricio Truchet

Simula los 5 contenedores inteligentes de San Francisco equipados con sensores ultrasónicos
de nivel, sondas térmicas y monitoreo de batería, transmitiendo lecturas en tiempo real
tanto a la nube de Google Firebase (Cloud Firestore) como vía MQTT municipal.
"""

import sys
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../../herramientas').resolve()))
import acceso_cli
import time
import json
import random
import argparse
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime

# Configurar salida segura en UTF-8 para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ID = "sf-residuos-urbanos-utn"
FIRESTORE_URL_BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/telemetria_contenedores"

# Catálogo oficial de Contenedores y Puntos Limpios de San Francisco (Córdoba)
CONTENEDORES = [
    {
        "id": "ECO-SF-001",
        "sensor_id": "SF-IOT-001",
        "nombre": "Ecopunto Plaza Cívica",
        "ubicacion": "Bv. 25 de Mayo y Libertador Norte",
        "altura_cm": 150.0,
        "coords": [-31.4288, -62.0825]
    },
    {
        "id": "ECO-SF-002",
        "sensor_id": "SF-IOT-002",
        "nombre": "Ecopunto Parque Cincuentenario",
        "ubicacion": "Av. Urquiza y Bv. Roca",
        "altura_cm": 180.0,
        "coords": [-31.4254, -62.0684]
    },
    {
        "id": "ECO-SF-003",
        "sensor_id": "SF-IOT-003",
        "nombre": "Ecopunto Paseo Cervantes",
        "ubicacion": "Av. Cervantes y Caseros",
        "altura_cm": 150.0,
        "coords": [-31.4283, -62.0985]
    },
    {
        "id": "ECO-SF-004",
        "sensor_id": "SF-IOT-004",
        "nombre": "Punto Verde UTN FRSFCO",
        "ubicacion": "Av. de la Universidad 501",
        "altura_cm": 140.0,
        "coords": [-31.4205, -62.1110]
    },
    {
        "id": "ECO-SF-005",
        "sensor_id": "SF-IOT-005",
        "nombre": "Ecopunto Barrio Sarmiento",
        "ubicacion": "López y Planes 950",
        "altura_cm": 160.0,
        "coords": [-31.4396, -62.0786]
    }
]

_acceso = {"token": None, "vence": 0}


def token_de_acceso():
    """Credencial de administración del CLI de Firebase (`firebase login`): las reglas solo dejan
    publicar telemetría a la autoridad, así que un sensor sin credencial es rechazado."""
    if time.time() > _acceso["vence"]:
        cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
        datos = urllib.parse.urlencode({
            "grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
            **acceso_cli.CLIENTE}).encode()
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", datos)))
        _acceso.update(token=r["access_token"], vence=time.time() + 3000)
    return _acceso["token"]


def enviar_a_firestore(contenedor_id, datos):
    """Envía la lectura de telemetría a Cloud Firestore mediante REST API."""
    url = f"{FIRESTORE_URL_BASE}/{contenedor_id}"
    cuerpo = {
        "fields": {
            "dispositivoId": {"stringValue": datos["sensor_id"]},
            "nombre": {"stringValue": datos["nombre"]},
            "ubicacion": {"stringValue": datos["ubicacion"]},
            "porcentajeLlenado": {"doubleValue": round(datos["llenado_pct"], 1)},
            "distanciaSensorCm": {"doubleValue": round(datos["distancia_cm"], 1)},
            "temperaturaCelsius": {"doubleValue": round(datos["temp_c"], 1)},
            "bateriaPorcentaje": {"integerValue": str(datos["bateria_pct"])},
            "alertaDesborde": {"booleanValue": datos["alerta_desborde"]},
            "alertaTemperatura": {"booleanValue": datos["alerta_temperatura"]},
            "coordsLat": {"doubleValue": datos["coords"][0]},
            "coordsLng": {"doubleValue": datos["coords"][1]},
            "ultimaActualizacion": {"stringValue": datetime.utcnow().isoformat() + "Z"}
        }
    }
    datos_bytes = json.dumps(cuerpo).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=datos_bytes,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token_de_acceso()}"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"  [Aviso Firestore] Error enviando lectura: {e}")
        return False

def simular_ciclo(c, forzar_desborde=False):
    """Genera una medición telemática verosímil y la transmite a la nube."""
    h_tot = c["altura_cm"]
    if forzar_desborde:
        dist = random.uniform(5.0, 15.0) # Nivel crítico próximo a la tapa
    else:
        dist = random.uniform(25.0, h_tot - 10.0)

    llenado_pct = max(0.0, min(100.0, ((h_tot - dist) / h_tot) * 100.0))
    temp_c = round(random.uniform(20.5, 27.8), 1)
    bat_pct = random.randint(88, 99)

    alerta_desborde = llenado_pct >= 80.0
    alerta_temp = temp_c >= 45.0

    datos = {
        "id": c["id"],
        "sensor_id": c["sensor_id"],
        "nombre": c["nombre"],
        "ubicacion": c["ubicacion"],
        "coords": c["coords"],
        "distancia_cm": dist,
        "llenado_pct": llenado_pct,
        "temp_c": temp_c,
        "bateria_pct": bat_pct,
        "alerta_desborde": alerta_desborde,
        "alerta_temperatura": alerta_temp
    }

    exito = enviar_a_firestore(c["id"], datos)
    estado_str = "ALERTA DESBORDE (>80%)" if alerta_desborde else "NOMINAL"
    cloud_str = "Cloud Firestore: Sincronizado" if exito else "Cloud Firestore: Desconectado"

    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {c['nombre']} ({c['sensor_id']}) -> Llenado: {llenado_pct:.1f}% [{estado_str}] | Temp: {temp_c}°C | Bat: {bat_pct}% | {cloud_str}")
    return datos

def main():
    parser = argparse.ArgumentParser(description="Simulador de Sensores IoT con Firestore Cloud - San Francisco Residuos")
    parser.add_argument("--intervalo", type=float, default=3.0, help="Segundos entre envíos telemáticos")
    parser.add_argument("--iteraciones", type=int, default=10, help="Cantidad de paquetes (0 = infinito)")
    parser.add_argument("--desborde", action="store_true", help="Fuerza nivel de llenado crítico en Plaza Cívica")
    args = parser.parse_args()

    print("=" * 80)
    print("  SIMULADOR TELEMÁTICO DE SENSORES IOT • CIUDAD DE SAN FRANCISCO")
    print(f"  Destino Cloud: Google Firebase Firestore ({PROJECT_ID})")
    print(f"  Frecuencia: {args.intervalo}s | Iteraciones: {args.iteraciones or 'Continuo'}")
    print("=" * 80)

    cuenta = 0
    try:
        while True:
            cuenta += 1
            c = CONTENEDORES[(cuenta - 1) % len(CONTENEDORES)]
            es_desborde = args.desborde and (c["id"] == "ECO-SF-001")
            simular_ciclo(c, forzar_desborde=es_desborde)

            if args.iteraciones > 0 and cuenta >= args.iteraciones:
                print("\n[OK] Simulación de sensores finalizada exitosamente.")
                break

            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[INFO] Simulación detenida por el usuario.")

if __name__ == "__main__":
    main()
