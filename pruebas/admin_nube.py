"""Acceso administrativo a Firestore (credenciales del CLI de Firebase) para verificar y limpiar datos de prueba."""
import json, pathlib, urllib.parse, urllib.request, urllib.error
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../herramientas').resolve()))
import acceso_cli
PROYECTO = "sf-residuos-urbanos-utn"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROYECTO}/databases/(default)/documents"

def _token():
    cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
    d = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
        **acceso_cli.CLIENTE}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", d)))["access_token"]

def listar(coleccion):
    r = urllib.request.Request(f"{BASE}/{coleccion}?pageSize=300", headers={"Authorization": f"Bearer {_token()}"})
    return json.load(urllib.request.urlopen(r)).get("documents", [])

def texto(doc):
    return json.dumps(doc.get("fields", {}), ensure_ascii=False)

def borrar_con_marca(marca, colecciones=("solicitudes_residuos", "notificaciones", "incidentes")):
    t = _token(); n = 0
    for c in colecciones:
        r = urllib.request.Request(f"{BASE}/{c}?pageSize=300", headers={"Authorization": f"Bearer {t}"})
        for d in json.load(urllib.request.urlopen(r)).get("documents", []):
            if marca in texto(d):
                urllib.request.urlopen(urllib.request.Request(f"https://firestore.googleapis.com/v1/{d['name']}", method="DELETE",
                    headers={"Authorization": f"Bearer {t}"})); n += 1
    return n


def llenado(contenedor):
    """Porcentaje de llenado guardado en la telemetría de un contenedor (None si no existe)."""
    req = urllib.request.Request(f"{BASE}/telemetria_contenedores/{contenedor}", headers={"Authorization": f"Bearer {_token()}"})
    try:
        campos = json.load(urllib.request.urlopen(req)).get("fields", {})
    except urllib.error.HTTPError:
        return None
    v = campos.get("porcentajeLlenado", {})
    return float(v.get("doubleValue", v.get("integerValue", 0))) if v else None


def restaurar_llenado(contenedor, pct):
    """Vuelve el contenedor al llenado que tenía antes de una prueba que lo vació."""
    if pct is None:
        return
    cuerpo = {"fields": {"porcentajeLlenado": {"doubleValue": pct}, "alertaDesborde": {"booleanValue": pct >= 80}}}
    req = urllib.request.Request(
        f"{BASE}/telemetria_contenedores/{contenedor}?updateMask.fieldPaths=porcentajeLlenado&updateMask.fieldPaths=alertaDesborde",
        json.dumps(cuerpo).encode(), method="PATCH",
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"})
    urllib.request.urlopen(req)


def borrar_documento(ruta):
    """Borra un documento puntual que dejó una prueba."""
    req = urllib.request.Request(f"{BASE}/{ruta}", method="DELETE", headers={"Authorization": f"Bearer {_token()}"})
    urllib.request.urlopen(req)
