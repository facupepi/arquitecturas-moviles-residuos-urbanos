#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servicio de ingesta de los sensores de los contenedores.

Se suscribe al intermediario MQTT, guarda cada lectura en Cloud Firestore (colección
telemetria_contenedores) y registra las alarmas de llenado y las desconexiones de los sensores.

Canales:
  sf/contenedores/{id}/telemetria   mediciones periódicas (QoS 1)
  sf/contenedores/{id}/alarma       alarmas urgentes, por ejemplo llenado de 80 % o más (QoS 1)
  sf/sensores/{cliente}/estado      "conectado" o el aviso de desconexión que publica el intermediario

Credencial para escribir en Firestore, en este orden:
  1. variable de entorno FIRESTORE_TOKEN (token OAuth de una cuenta de servicio),
  2. credenciales por defecto de Google (google-auth), como en un clúster con identidad de carga de trabajo,
  3. en una computadora de desarrollo, la sesión del CLI de Firebase (`firebase login`).
Con --sin-nube solo procesa y muestra los mensajes.

Uso: python worker_ingesta_mqtt.py --broker localhost --ca ca.crt --usuario ingesta --clave ...
(también por variables de entorno BROKER_HOST, BROKER_PUERTO, MQTT_CA, MQTT_USUARIO y MQTT_CLAVE)
"""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROYECTO = os.environ.get("FIRESTORE_PROYECTO", "sf-residuos-urbanos-utn")
BASE = f"https://firestore.googleapis.com/v1/projects/{PROYECTO}/databases/(default)/documents/telemetria_contenedores"
UMBRAL_LLENADO = 80.0
_acceso = {"token": None, "vence": 0}
sin_nube = False


def token_de_acceso():
    if os.environ.get("FIRESTORE_TOKEN"):
        return os.environ["FIRESTORE_TOKEN"]
    if time.time() < _acceso["vence"]:
        return _acceso["token"]
    try:
        import google.auth
        import google.auth.transport.requests
        cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/datastore"])
        cred.refresh(google.auth.transport.requests.Request())
        _acceso.update(token=cred.token, vence=time.time() + 3000)
        return cred.token
    except Exception:
        pass
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent / "../../herramientas").resolve()))
    import acceso_cli
    cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
    datos = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
                                    **acceso_cli.CLIENTE}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", datos)))
    _acceso.update(token=r["access_token"], vence=time.time() + 3000)
    return _acceso["token"]


def guardar(contenedor_id, campos):
    """Actualiza solo los campos indicados del documento del contenedor."""
    if sin_nube:
        return True
    try:
        token = token_de_acceso()
    except Exception:
        print("  [FIRESTORE] Sin credencial para escribir: la lectura se procesó pero no se guardó.")
        return False
    mascara = "&".join("updateMask.fieldPaths=" + urllib.parse.quote(k) for k in campos)
    req = urllib.request.Request(f"{BASE}/{urllib.parse.quote(contenedor_id)}?{mascara}",
                                 json.dumps({"fields": campos}).encode(), method="PATCH",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"  [FIRESTORE] No se pudo guardar {contenedor_id}: {e}")
        return False


def procesar_telemetria(cid, data):
    tel = data.get("telemetria", {})
    llenado = float(tel.get("porcentaje_llenado", 0.0))
    if not 0 <= llenado <= 100:
        print(f"  [DESCARTADA] {cid}: llenado fuera de rango ({llenado})")
        return False
    campos = {
        "dispositivoId": {"stringValue": str(data.get("dispositivo_id", ""))},
        "nombre": {"stringValue": str(data.get("nombre_punto", cid))},
        "porcentajeLlenado": {"doubleValue": round(llenado, 1)},
        "distanciaSensorCm": {"doubleValue": float(tel.get("distancia_sensor_cm", 0.0))},
        "temperaturaCelsius": {"doubleValue": float(tel.get("temperatura_celsius", 0.0))},
        "bateriaPorcentaje": {"integerValue": str(int(tel.get("bateria_porcentaje", 0)))},
        "alertaDesborde": {"booleanValue": llenado >= UMBRAL_LLENADO},
        "alertaTemperatura": {"booleanValue": float(tel.get("temperatura_celsius", 0.0)) >= 45.0},
        "ultimaActualizacion": {"stringValue": datetime.now(timezone.utc).isoformat()},
    }
    ok = guardar(cid, campos)
    print(f"  [LECTURA] {cid}: {llenado:.1f} % de llenado, guardada en Firestore: {'sí' if ok else 'no'}")
    return ok


def procesar_alarma(cid, data):
    print(f"  [ALARMA] {cid}: {data.get('motivo', 'sin motivo')} ({data.get('porcentaje_llenado', '?')} %). "
          "La parada queda marcada como urgente en la hoja de ruta.")
    return guardar(cid, {"alertaDesborde": {"booleanValue": True},
                         "ultimaActualizacion": {"stringValue": datetime.now(timezone.utc).isoformat()}})


def al_conectar(cliente, userdata, flags, codigo, propiedades=None):
    if codigo == 0:
        # Suscripción compartida: si hay varias réplicas del servicio, el intermediario reparte los mensajes entre ellas
        for canal in ("sf/contenedores/+/telemetria", "sf/contenedores/+/alarma", "sf/sensores/+/estado"):
            cliente.subscribe(f"$share/ingesta/{canal}", qos=1)
        print("[INGESTA] Conectada al intermediario y suscrita a mediciones, alarmas y estado de los sensores.")
    else:
        print(f"[INGESTA] Conexión rechazada: {codigo}")


def al_recibir(cliente, userdata, msg):
    partes = msg.topic.split("/")  # el canal llega sin el prefijo de la suscripción compartida
    try:
        data = json.loads(msg.payload.decode("utf-8") or "{}")
    except ValueError:
        print(f"  [DESCARTADO] Mensaje ilegible en {msg.topic}")
        return
    if partes[:2] == ["sf", "contenedores"] and len(partes) == 4:
        cid = partes[2]
        (procesar_telemetria if partes[3] == "telemetria" else procesar_alarma)(cid, data)
    elif partes[:2] == ["sf", "sensores"]:
        estado = data.get("estado", "?")
        print(f"  [ESTADO] Sensor {partes[2]}: {estado}" + (" (aviso de desconexión del intermediario)" if estado == "desconectado" else ""))


def main():
    global sin_nube
    ap = argparse.ArgumentParser(description="Servicio de ingesta MQTT de los contenedores")
    ap.add_argument("--broker", default=os.environ.get("BROKER_HOST", "localhost"))
    ap.add_argument("--puerto", type=int, default=int(os.environ.get("BROKER_PUERTO", "8883")))
    ap.add_argument("--ca", default=os.environ.get("MQTT_CA"), help="certificado de la autoridad que firmó al intermediario (activa TLS)")
    ap.add_argument("--usuario", default=os.environ.get("MQTT_USUARIO"))
    ap.add_argument("--clave", default=os.environ.get("MQTT_CLAVE"))
    ap.add_argument("--sin-nube", action="store_true", help="no escribe en Firestore")
    a = ap.parse_args()
    sin_nube = a.sin_nube
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ingesta-sf-{os.getpid()}")
    cliente.on_connect = al_conectar
    cliente.on_message = al_recibir
    if a.usuario:
        cliente.username_pw_set(a.usuario, a.clave)
    if a.ca:
        cliente.tls_set(ca_certs=a.ca)
    cliente.connect(a.broker, a.puerto, 60)
    print(f"[INGESTA] Escuchando en {a.broker}:{a.puerto}")
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
