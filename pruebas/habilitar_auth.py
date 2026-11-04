"""Inicializa Firebase Auth y habilita email/contraseña en el proyecto, con las credenciales del CLI de Firebase."""
import json, pathlib, urllib.request, urllib.parse, sys
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../herramientas').resolve()))
import acceso_cli
PROYECTO = "sf-residuos-urbanos-utn"
cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
refresh = cfg["tokens"]["refresh_token"]
# credenciales públicas del cliente OAuth de firebase-tools
datos = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh,
    **acceso_cli.CLIENTE}).encode()
tok = json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", datos)))["access_token"]

def llamar(metodo, url, cuerpo=None):
    req = urllib.request.Request(url, json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "X-Goog-User-Project": PROYECTO})
    try:
        with urllib.request.urlopen(req) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:400]

print(llamar("POST", f"https://identitytoolkit.googleapis.com/v2/projects/{PROYECTO}/identityPlatform:initializeAuth", {}))
print(llamar("PATCH", f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROYECTO}/config?updateMask=signIn.email.enabled,signIn.email.passwordRequired",
    {"signIn": {"email": {"enabled": True, "passwordRequired": True}}}))
