#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emisor de notificaciones push (Firebase Cloud Messaging) para San Francisco Residuos.

Los dispositivos se registran solos desde la app (colección `dispositivos`, el id es el token de FCM).
Este emisor lee esos tokens y envía el aviso aunque la app esté cerrada. Usa las credenciales de
administración del CLI de Firebase (`firebase login`); en producción sería un servicio del clúster
o una Cloud Function con su propia cuenta de servicio.

  python enviar_push.py --titulo "Jornada de limpieza" --mensaje "Sábado 9 h en Plaza Cívica"
  python enviar_push.py --titulo ... --mensaje ... --rol ciudadano
  python enviar_push.py --vigilar            # avisa solo cuando hay una campaña nueva o cambia una solicitud
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../../herramientas').resolve()))
import acceso_cli

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROYECTO = "sf-residuos-urbanos-utn"
FIRESTORE = f"https://firestore.googleapis.com/v1/projects/{PROYECTO}/databases/(default)/documents"
FCM = f"https://fcm.googleapis.com/v1/projects/{PROYECTO}/messages:send"
_acceso = {"token": None, "vence": 0}

TEXTO_ESTADO = {
    "en_camino": ("Tu retiro está en camino", "Una cuadrilla fue asignada a tu solicitud."),
    "recolectado": ("Retiro realizado", "Recolectamos tu solicitud. ¡Gracias por cuidar San Francisco!"),
    "cancelado": ("Solicitud cancelada", "Tu solicitud de retiro fue cancelada."),
}


def token_de_acceso():
    if time.time() > _acceso["vence"]:
        cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
        datos = urllib.parse.urlencode({
            "grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
            **acceso_cli.CLIENTE}).encode()
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", datos)))
        _acceso.update(token=r["access_token"], vence=time.time() + 3000)
    return _acceso["token"]


def pedir(url, cuerpo=None, metodo=None):
    req = urllib.request.Request(url, json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
                                 headers={"Authorization": f"Bearer {token_de_acceso()}", "Content-Type": "application/json",
                                          "X-Goog-User-Project": PROYECTO})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r) if r.length != 0 else {}


def listar(coleccion):
    docs, pagina = [], ""
    while True:
        r = pedir(f"{FIRESTORE}/{coleccion}?pageSize=300{pagina}")
        docs += r.get("documents", [])
        if not r.get("nextPageToken"):
            return docs
        pagina = "&pageToken=" + r["nextPageToken"]


def valor(campo):
    return next(iter(campo.values())) if campo else None


def dispositivos(rol=None, uid=None):
    """Tokens registrados, opcionalmente filtrados por rol o por usuario."""
    out = []
    for d in listar("dispositivos"):
        f = d.get("fields", {})
        if rol and valor(f.get("rol")) != rol:
            continue
        if uid and valor(f.get("uid")) != uid:
            continue
        out.append(d["name"].rsplit("/", 1)[-1])
    return out


def enviar(tokens, titulo, cuerpo, tag=None):
    """Envía el aviso a cada token. Devuelve (enviados, descartados)."""
    ok = malos = 0
    for t in tokens:
        mensaje = {"message": {"token": t, "data": {"titulo": titulo, "cuerpo": cuerpo, **({"tag": tag} if tag else {})},
                               "webpush": {"headers": {"Urgency": "high", "TTL": "3600"}}}}
        for intento in (1, 2):
            try:
                pedir(FCM, mensaje, "POST")
                ok += 1
                break
            except urllib.error.HTTPError as e:
                detalle = e.read().decode()
                inexistente = e.code == 404 or "UNREGISTERED" in detalle or "INVALID_ARGUMENT" in detalle
                if inexistente and intento == 1:
                    time.sleep(3)  # un registro recién creado puede tardar en propagarse: se reintenta una vez
                    continue
                if inexistente:
                    try:  # el dispositivo ya no existe: se limpia
                        pedir(f"{FIRESTORE}/dispositivos/{urllib.parse.quote(t, safe='')}", metodo="DELETE")
                    except Exception:
                        pass
                    malos += 1
                else:
                    print(f"  [Aviso] FCM respondió {e.code}: {detalle[:200]}")
                break
    return ok, malos


def vigilar(intervalo):
    """Envía push cuando aparece una campaña nueva o una solicitud cambia de estado."""
    vistas = {d["name"] for d in listar("notificaciones")}
    estados = {d["name"]: valor(d["fields"].get("estado")) for d in listar("solicitudes_residuos")}
    print(f"Vigilando campañas ({len(vistas)} existentes) y {len(estados)} solicitudes. Ctrl+C para salir.")
    while True:
        time.sleep(intervalo)
        for d in listar("notificaciones"):
            if d["name"] in vistas:
                continue
            vistas.add(d["name"])
            f = d["fields"]
            titulo, mensaje = valor(f.get("titulo")) or "Aviso municipal", valor(f.get("desc")) or ""
            print("Campaña nueva ->", titulo, enviar(dispositivos(), titulo, mensaje))
        for d in listar("solicitudes_residuos"):
            f, antes, ahora = d["fields"], estados.get(d["name"]), valor(d["fields"].get("estado"))
            estados[d["name"]] = ahora
            if antes is not None and ahora != antes and ahora in TEXTO_ESTADO:
                titulo, mensaje = TEXTO_ESTADO[ahora]
                print("Solicitud", ahora, "->", enviar(dispositivos(uid=valor(f.get("usuarioId"))), titulo, mensaje))


def main():
    ap = argparse.ArgumentParser(description="Emisor de push de San Francisco Residuos")
    ap.add_argument("--titulo")
    ap.add_argument("--mensaje")
    ap.add_argument("--rol", choices=["ciudadano", "autoridad", "recolector"])
    ap.add_argument("--vigilar", action="store_true")
    ap.add_argument("--intervalo", type=float, default=5.0)
    a = ap.parse_args()
    if a.vigilar:
        vigilar(a.intervalo)
        return
    if not (a.titulo and a.mensaje):
        ap.error("indicá --titulo y --mensaje, o usá --vigilar")
    tokens = dispositivos(rol=a.rol)
    print(f"{len(tokens)} dispositivos registrados")
    ok, malos = enviar(tokens, a.titulo, a.mensaje)
    print(f"Enviados: {ok} | descartados por inválidos: {malos}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
