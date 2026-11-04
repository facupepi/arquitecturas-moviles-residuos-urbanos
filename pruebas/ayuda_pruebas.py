"""Cuentas temporales para las pruebas automáticas.

Cada ejecución crea una cuenta por rol (vecino, autoridad con claim, cuadrilla con claim) con clave aleatoria,
las usa y las borra al terminar. No hay contraseñas fijas en el repositorio ni en el sitio.
"""
import atexit, json, pathlib, re, secrets, urllib.error, urllib.parse, urllib.request
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../herramientas').resolve()))
import acceso_cli

PROYECTO = "sf-residuos-urbanos-utn"
RAIZ = pathlib.Path(__file__).resolve().parent.parent
API_KEY = re.search(r'"apiKey": "([^"]+)"', (RAIZ / "app/firebase-config.js").read_text(encoding="utf-8")).group(1)
CLAIM = {"ciudadano": None, "autoridad": "autoridad", "recolector": "recolector"}
NOMBRE = {"ciudadano": "Vecino de Prueba", "autoridad": "Dirección de Servicios Públicos", "recolector": "Cuadrilla Móvil 03"}
_cuentas = {}


def _acceso():
    cfg = json.loads((pathlib.Path.home() / ".config/configstore/firebase-tools.json").read_text())
    d = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
        **acceso_cli.CLIENTE}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", d)))["access_token"]


def _admin(ruta, cuerpo):
    req = urllib.request.Request(f"https://identitytoolkit.googleapis.com/v1/projects/{PROYECTO}{ruta}",
        json.dumps(cuerpo).encode(), method="POST",
        headers={"Authorization": f"Bearer {_acceso()}", "Content-Type": "application/json", "X-Goog-User-Project": PROYECTO})
    return json.load(urllib.request.urlopen(req))


def cuenta(rol):
    """Devuelve (correo, clave, uid) de la cuenta temporal del rol, creándola si hace falta."""
    if rol not in _cuentas:
        correo, clave = f"e2e-{rol}-{secrets.token_hex(3)}@prueba.invalid", secrets.token_urlsafe(16)
        claims = json.dumps({"rol": CLAIM[rol]}) if CLAIM[rol] else "{}"
        r = _admin("/accounts", {"email": correo, "password": clave, "displayName": NOMBRE[rol],
                                 "emailVerified": True})
        if CLAIM[rol]:  # la creación ignora los claims: se asignan con una actualización
            _admin("/accounts:update", {"localId": r["localId"], "customAttributes": claims})
        _cuentas[rol] = (correo, clave, r["localId"])
    return _cuentas[rol]


def token(rol):
    """(idToken, uid) para llamar a la API REST de Firestore como ese rol."""
    correo, clave, _ = cuenta(rol)
    req = urllib.request.Request(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
        json.dumps({"email": correo, "password": clave, "returnSecureToken": True}).encode(),
        {"Content-Type": "application/json", "Referer": "https://sf-residuos-urbanos-utn.web.app/"})
    d = json.load(urllib.request.urlopen(req))
    return d["idToken"], d["localId"]


def ingresar(pg, rol, espera=1500):
    """Inicia sesión en la página como ese rol y espera a que la interfaz del rol esté lista."""
    if pg.evaluate("!!localStorage.getItem('SF_RESIDUOS_AUTH_SESSION_V2')"):  # cambiar de cuenta exige cerrar la sesión activa
        pg.evaluate("cerrarSesion()")
        pg.wait_for_timeout(2500)
    correo, clave, _ = cuenta(rol)
    pg.evaluate("([e, c]) => firebase.auth().signInWithEmailAndPassword(e, c).then(() => true)", [correo, clave])
    pg.wait_for_function("document.body.classList.contains('autenticado')", timeout=15000)
    pg.wait_for_timeout(espera)


def borrar_cuentas():
    for rol, (_, _, uid) in list(_cuentas.items()):
        try:
            _admin("/accounts:delete", {"localId": uid})
        except Exception:
            pass
    _cuentas.clear()


atexit.register(borrar_cuentas)
