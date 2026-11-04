"""Credenciales OAuth del CLI de Firebase, leídas de la instalación local de firebase-tools.

Los scripts de administración (pruebas, simulador de sensores, emisor de push) piden un token de acceso con la
sesión de `firebase login`. El identificador y el secreto del cliente OAuth pertenecen a firebase-tools y no se
copian en este repositorio: se leen de su instalación o de las variables FIREBASE_CLI_CLIENT_ID y
FIREBASE_CLI_CLIENT_SECRET.
"""
import os, pathlib, re, shutil, subprocess


def _buscar():
    raices = []
    try:
        raices.append(pathlib.Path(subprocess.run("npm root -g", capture_output=True, text=True, shell=True).stdout.strip()))
    except Exception:
        pass
    exe = shutil.which("firebase")
    if exe:
        raices.append(pathlib.Path(exe).resolve().parent / "node_modules")
    for raiz in raices:
        api = raiz / "firebase-tools/lib/api.js"
        if api.exists():
            t = api.read_text(encoding="utf-8")
            i = re.search(r'const clientId = \(\) => utils\.envOverride\([^,]+,\s*"([^"]+)"', t)
            s = re.search(r'const clientSecret = \(\) => utils\.envOverride\([^,]+,\s*"([^"]+)"', t)
            if i and s:
                return i.group(1), s.group(1)
    raise RuntimeError("No se encontraron las credenciales del CLI: instalá firebase-tools o definí "
                       "FIREBASE_CLI_CLIENT_ID y FIREBASE_CLI_CLIENT_SECRET")


def _cliente():
    if os.environ.get("FIREBASE_CLI_CLIENT_ID") and os.environ.get("FIREBASE_CLI_CLIENT_SECRET"):
        return os.environ["FIREBASE_CLI_CLIENT_ID"], os.environ["FIREBASE_CLI_CLIENT_SECRET"]
    return _buscar()


_id, _secreto = _cliente()
CLIENTE = {"client_id": _id, "client_secret": _secreto}
