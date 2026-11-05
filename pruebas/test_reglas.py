"""Prueba las reglas de seguridad de Firestore publicadas, con cuentas reales de cada rol y sin sesión.

Los documentos de prueba llevan la marca E2E-PRUEBA y se eliminan al finalizar.
"""
import json, pathlib, re, sys, urllib.error, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import admin_nube, ayuda_pruebas

HTML = (pathlib.Path(__file__).resolve().parent.parent / "app/firebase-config.js").read_text(encoding="utf-8")
API_KEY = re.search(r'"apiKey": "([^"]+)"', HTML).group(1)
BASE = admin_nube.BASE
res = []

def chk(n, c, e=""):
    res.append(bool(c)); print("OK   " if c else "FALLA", n, e)

def llamar(metodo, ruta, cuerpo=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = f"Bearer {tok}"
    r = urllib.request.Request(BASE + ruta, json.dumps(cuerpo).encode() if cuerpo is not None else None, h, method=metodo)
    try:
        with urllib.request.urlopen(r) as x: return x.status
    except urllib.error.HTTPError as e: return e.code

S = lambda v: {"stringValue": v}
def solicitud(uid, estado="pendiente", tipo="voluminoso"):
    return {"fields": {"usuarioId": S(uid), "estado": S(estado), "tipoResiduo": S(tipo), "direccion": S("Av. Urquiza 100 E2E-PRUEBA"),
            "fechaCreacion": {"timestampValue": "2026-11-04T00:00:00Z"}, "solicitudId": S("SOL-E2E")}}

def incidente(uid):
    return {"fields": {"incidenteId": S("INC-E2E"), "tipo": S("Contenedor dañado o roto"), "ubicacion": S("Av. Cervantes E2E-PRUEBA"),
            "gravedad": S("media"), "estado": S("abierto"), "creadoPor": S(uid), "descripcion": S("E2E-PRUEBA")}}

try:
    tV, uV = ayuda_pruebas.token("ciudadano")
    tA, _ = ayuda_pruebas.token("autoridad")
    tC, uC = ayuda_pruebas.token("recolector")

    # --- Sin sesión
    chk("Anónimo no puede crear solicitudes", llamar("POST", "/solicitudes_residuos?documentId=e2e-anon", solicitud("x")) == 403)
    chk("Anónimo no puede leer solicitudes", llamar("GET", "/solicitudes_residuos") == 403)
    chk("Anónimo no puede escribir ecopuntos", llamar("PATCH", "/ecopuntos/e2e", {"fields": {"a": S("1")}}) == 403)
    chk("Anónimo no puede crear incidentes", llamar("POST", "/incidentes?documentId=e2e-anon", {"fields": {"tipo": S("E2E-PRUEBA")}}) == 403)
    chk("Anónimo no puede difundir campañas", llamar("POST", "/notificaciones?documentId=e2e-anon", {"fields": {"titulo": S("E2E-PRUEBA")}}) == 403)
    chk("Anónimo no puede borrar telemetría", llamar("DELETE", "/telemetria_contenedores/ECO-SF-001") == 403)
    chk("Telemetría válida sin sesión rechazada", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"porcentajeLlenado": {"doubleValue": 50}}}) == 403)
    chk("Telemetría fuera de rango sin sesión rechazada", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"porcentajeLlenado": {"doubleValue": 500}}}) == 403)

    chk("Anónimo no puede leer incidentes", llamar("GET", "/incidentes") == 403)

    # --- Vecino
    chk("Vecino crea su propia solicitud", llamar("POST", "/solicitudes_residuos?documentId=e2e-vecino", solicitud(uV), tV) == 200)
    chk("Vecino no puede crear solicitudes a nombre de otro", llamar("POST", "/solicitudes_residuos?documentId=e2e-ajena", solicitud("otro-uid"), tV) == 403)
    chk("Vecino no puede crear una solicitud ya despachada", llamar("POST", "/solicitudes_residuos?documentId=e2e-desp", solicitud(uV, "en_camino"), tV) == 403)
    chk("Vecino no puede crear un tipo de residuo inválido", llamar("POST", "/solicitudes_residuos?documentId=e2e-tipo", solicitud(uV, tipo="radiactivo"), tV) == 403)
    chk("Vecino no puede marcar como retirada su solicitud",
        llamar("PATCH", "/solicitudes_residuos/e2e-vecino?updateMask.fieldPaths=estado", {"fields": {"estado": S("recolectado")}}, tV) == 403)
    chk("Vecino no puede asignarse una cuadrilla",
        llamar("PATCH", "/solicitudes_residuos/e2e-vecino?updateMask.fieldPaths=cuadrilla", {"fields": {"cuadrilla": S("Móvil 03")}}, tV) == 403)
    chk("Vecino no puede agregar campos extra", llamar("POST", "/solicitudes_residuos?documentId=e2e-extra",
        {"fields": dict(solicitud(uV)["fields"], pesoRealKg={"doubleValue": 99})}, tV) == 403)
    chk("Vecino no puede usar un código con caracteres raros", llamar("POST", "/solicitudes_residuos?documentId=e2e-cod",
        {"fields": dict(solicitud(uV)["fields"], solicitudId=S("SOL-<img src=x>"))}, tV) == 403)
    chk("Vecino crea y cancela otra solicitud", llamar("POST", "/solicitudes_residuos?documentId=e2e-cancela", solicitud(uV), tV) == 200 and
        llamar("PATCH", "/solicitudes_residuos/e2e-cancela?updateMask.fieldPaths=estado", {"fields": {"estado": S("cancelado")}}, tV) == 200)
    chk("Vecino no crea incidentes con gravedad inválida", llamar("POST", "/incidentes?documentId=e2e-incv",
        {"fields": dict(incidente(uV)["fields"], gravedad=S("<b>alta</b>"))}, tV) == 403)
    chk("Vecino no crea incidentes a nombre de otro", llamar("POST", "/incidentes?documentId=e2e-incv2", incidente("otro-uid"), tV) == 403)
    chk("Vecino no puede listar todas las solicitudes", llamar("GET", "/solicitudes_residuos", None, tV) == 403)
    chk("Vecino no puede borrar solicitudes", llamar("DELETE", "/solicitudes_residuos/e2e-vecino", None, tV) == 403)
    chk("Vecino no puede difundir campañas", llamar("POST", "/notificaciones?documentId=e2e-v", {"fields": {"titulo": S("E2E-PRUEBA")}}, tV) == 403)
    chk("Vecino no puede publicar telemetría", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"porcentajeLlenado": {"doubleValue": 50}}}, tV) == 403)
    chk("Vecino no puede escribir ecopuntos", llamar("PATCH", "/ecopuntos/e2e", {"fields": {"a": S("1")}}, tV) == 403)

    # --- Dispositivos para push
    disp = lambda uid, rol="ciudadano": {"fields": {"uid": S(uid), "rol": S(rol), "actualizado": {"timestampValue": "2026-11-04T00:00:00Z"}}}
    chk("Anónimo no puede registrar dispositivos", llamar("PATCH", "/dispositivos/e2e-token", disp("x")) == 403)
    chk("Vecino registra su propio dispositivo", llamar("PATCH", "/dispositivos/e2e-token", disp(uV), tV) == 200)
    chk("Vecino no puede declararse autoridad en su dispositivo", llamar("PATCH", "/dispositivos/e2e-rol", disp(uV, "autoridad"), tV) == 403)
    chk("Vecino no puede registrar un dispositivo a nombre de otro", llamar("PATCH", "/dispositivos/e2e-otro", disp("otro-uid"), tV) == 403)
    chk("Nadie puede listar los dispositivos desde el cliente", llamar("GET", "/dispositivos", None, tV) == 403)
    chk("Vecino registra un segundo dispositivo", llamar("PATCH", "/dispositivos/e2e-tok2", disp(uV), tV) == 200)
    chk("Vecino quita su dispositivo", llamar("DELETE", "/dispositivos/e2e-token", None, tV) == 200)

    # --- Cuadrilla
    chk("Cuadrilla puede leer solicitudes", llamar("GET", "/solicitudes_residuos", None, tC) == 200)
    chk("Cuadrilla confirma recolección (campos operativos)",
        llamar("PATCH", "/solicitudes_residuos/e2e-vecino?updateMask.fieldPaths=estado&updateMask.fieldPaths=pesoRealKg",
               {"fields": {"estado": S("recolectado"), "pesoRealKg": {"doubleValue": 12}}}, tC) == 200)
    chk("Cuadrilla no puede modificar el domicilio de una solicitud",
        llamar("PATCH", "/solicitudes_residuos/e2e-vecino?updateMask.fieldPaths=direccion", {"fields": {"direccion": S("Otra calle E2E-PRUEBA")}}, tC) == 403)
    chk("Cuadrilla no puede difundir campañas", llamar("POST", "/notificaciones?documentId=e2e-c", {"fields": {"titulo": S("E2E-PRUEBA")}}, tC) == 403)
    chk("Cuadrilla reporta un incidente", llamar("POST", "/incidentes?documentId=e2e-inc", incidente(uC), tC) == 200)
    chk("Cuadrilla no cambia el tipo de un incidente", llamar("PATCH", "/incidentes/e2e-inc?updateMask.fieldPaths=tipo", {"fields": {"tipo": S("Otro E2E-PRUEBA")}}, tC) == 403)
    chk("Cuadrilla toma un incidente", llamar("PATCH", "/incidentes/e2e-inc?updateMask.fieldPaths=estado", {"fields": {"estado": S("en_atencion")}}, tC) == 200)
    chk("Cuadrilla no borra incidentes", llamar("DELETE", "/incidentes/e2e-inc", None, tC) == 403)
    chk("Cuadrilla no toma el dispositivo de otra persona", llamar("PATCH", "/dispositivos/e2e-tok2", disp(uC, "recolector"), tC) == 403)
    chk("Cuadrilla registra su dispositivo con su rol", llamar("PATCH", "/dispositivos/e2e-tok3", disp(uC, "recolector"), tC) == 200)
    llamar("DELETE", "/dispositivos/e2e-tok3", None, tC)

    # --- Autoridad
    chk("Autoridad lee todas las solicitudes", llamar("GET", "/solicitudes_residuos", None, tA) == 200)
    chk("Autoridad despacha una solicitud", llamar("PATCH", "/solicitudes_residuos/e2e-vecino?updateMask.fieldPaths=cuadrilla", {"fields": {"cuadrilla": S("Móvil 03")}}, tA) == 200)
    chk("Autoridad publica telemetría válida", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"porcentajeLlenado": {"doubleValue": 50}}}, tA) == 200)
    chk("Autoridad: telemetría fuera de rango rechazada", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"porcentajeLlenado": {"doubleValue": 500}}}, tA) == 403)
    chk("Autoridad: campo no permitido en telemetría rechazado", llamar("PATCH", "/telemetria_contenedores/e2e", {"fields": {"intruso": S("1")}}, tA) == 403)
    llamar("DELETE", "/telemetria_contenedores/e2e", None, tA)
    chk("Autoridad difunde una campaña", llamar("POST", "/notificaciones?documentId=e2e-a", {"fields": {"titulo": S("E2E-PRUEBA"), "campanaId": S("CMP-E2E")}}, tA) == 200)
    chk("Autoridad resuelve un incidente", llamar("PATCH", "/incidentes/e2e-inc?updateMask.fieldPaths=estado", {"fields": {"estado": S("resuelto")}}, tA) == 200)
    chk("Autoridad borra un incidente", llamar("DELETE", "/incidentes/e2e-inc", None, tA) == 200)
finally:
    llamar("DELETE", "/dispositivos/e2e-tok2", None, tV)
    try:
        n = admin_nube.borrar_con_marca("E2E-PRUEBA") + admin_nube.borrar_con_marca("SOL-E2E") + admin_nube.borrar_con_marca("INC-E2E")
        print("limpieza:", n, "documentos")
    except Exception as e:
        print("(no se pudo limpiar:", str(e)[:80], ")")

print(f"\n{sum(res)}/{len(res)} verificaciones OK")
sys.exit(0 if all(res) else 1)
