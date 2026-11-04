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
