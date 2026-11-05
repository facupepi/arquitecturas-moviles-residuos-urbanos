"""E2E contra la consigna del caso de estudio. Uso: test_consigna.py [URL]  (sin URL levanta servidor local)."""
import json, subprocess, sys, time, pathlib, urllib.request
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str((_pl.Path(__file__).resolve().parent / '../herramientas').resolve()))
import acceso_cli
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright
import ayuda_pruebas

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8767/index.html"
srv = None
if len(sys.argv) == 1:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8767", "-d", str(RAIZ)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)

res, errs = [], []

def admin_get(coleccion):
    import pathlib as P, urllib.parse as U
    cfg = json.loads((P.Path.home() / ".config/configstore/firebase-tools.json").read_text())
    d = U.urlencode({"grant_type": "refresh_token", "refresh_token": cfg["tokens"]["refresh_token"],
        **acceso_cli.CLIENTE}).encode()
    t = json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", d)))["access_token"]
    r = urllib.request.Request(f"https://firestore.googleapis.com/v1/projects/sf-residuos-urbanos-utn/databases/(default)/documents/{coleccion}?pageSize=300",
        headers={"Authorization": f"Bearer {t}"})
    return json.load(urllib.request.urlopen(r)).get("documents", [])
def chk(nombre, cond, extra=""):
    res.append((nombre, bool(cond)))
    print(("OK   " if cond else "FALLA"), nombre, extra)

ROL_DE = {"ciudadano": "ciudadano", "autoridad": "autoridad", "cuadrilla": "recolector"}  # etiquetas de rol

def login(pg, email, clave=None):
    ayuda_pruebas.ingresar(pg, ROL_DE[email], 1200)

def salir(pg):
    pg.evaluate("cerrarSesion()"); pg.wait_for_timeout(600)

import admin_nube
previo_llenado = admin_nube.llenado("ECO-SF-001")   # la cuadrilla lo vacía durante la prueba
try:
    with sync_playwright() as p:
        nav = p.chromium.launch()
        ctx = nav.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
        dialogos = []; pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
        pg.goto(URL, wait_until="load"); pg.wait_for_timeout(1500)
        chk("Arranca en pantalla de login (sin sesión automática)", pg.locator("#btn-google-login").is_visible())

        chk("Header sin usuario falso antes de ingresar", not pg.locator("#header-sesion").is_visible())

        # 1. CIUDADANO
        login(pg, "ciudadano")
        pg.wait_for_timeout(1500)
        ir = lambda x: (pg.evaluate("mostrarPantalla('%s')" % x), pg.wait_for_timeout(300))
        visible = lambda i: pg.evaluate("(i)=>{const e=document.getElementById(i);return !!e && e.offsetParent!==null}", i)
        chk("Ciudadano: no ve controles de sensores ni panel municipal", not visible("panel-iot-card") and not visible("btn-forzar-desborde-ui") and not visible("seccion-kpis-muni"))
        ir("contenedores")
        chk("Ciudadano: ve los horarios de recolección por zona", visible("tabla-cronograma-vecino") and pg.locator("#tabla-cronograma-vecino tr").count() >= 3)
        r = pg.evaluate("""()=>{const base={id:'B',coords:COORDS_SF};let ok=true,mejoras=0;
            for(let k=0;k<40;k++){const ds=Array.from({length:8},(_,i)=>({id:'P'+i,coords:[-31.4290+(Math.random()-.5)*.03,-62.0820+(Math.random()-.5)*.04]}));
              const t=resolverTSP(base,ds); if(t.distanciaKm>t.distanciaInicialKm+1e-6) ok=false; if(t.distanciaKm<t.distanciaInicialKm-1e-6) mejoras++; if(t.ruta.length!==ds.length+2) ok=false}
            return {ok,mejoras}}""")
        chk("Ruta: 2-opt nunca empeora el vecino más cercano y lo mejora en varios casos", r["ok"] and r["mejoras"] > 0, str(r))
        ir("contenedores")
        chk("Ciudadano: ve disponibilidad de contenedores", visible("lista-disponibilidad-vecino") and pg.locator("#lista-disponibilidad-vecino > div").count() >= 5)
        ir("mapa"); pg.wait_for_timeout(1500)
        chk("Ciudadano: mapa con teselas", pg.locator(".leaflet-tile").count() > 0)
        chk("Ciudadano: marcadores de ecopuntos", pg.locator(".leaflet-marker-icon, .leaflet-interactive").count() >= 5)
        ir("contenedores")
        chk("Ciudadano: ve el horario de atención de cada ecopunto", pg.locator("#lista-disponibilidad-vecino").inner_text().count("Atención:") == 5)
        chk("Ciudadano: ve niveles de contenedores", pg.evaluate("estadoApp.ecopuntos.length") >= 5)
        antes = pg.evaluate("estadoApp.solicitudes.length")
        pg.evaluate("abrirModalRegistro()")
        pg.check("input[name=tipo_residuo][value=voluminoso]")
        pg.evaluate("actualizarSubcategoriasFormulario('voluminoso')")
        pg.select_option("#reg-subcategoria", index=0)
        pg.fill("#reg-cantidad", "3"); pg.fill("#reg-direccion", "Bv. 25 de Mayo 1234 E2E-PRUEBA"); pg.fill("#reg-observaciones", "E2E-PRUEBA")
        pg.evaluate("document.getElementById('reg-fecha').value || (document.getElementById('reg-fecha').value=new Date(Date.now()+864e5).toISOString().slice(0,10))")
        pg.evaluate("document.getElementById('form-registro-residuo').requestSubmit()"); pg.wait_for_timeout(800)
        chk("Ciudadano: registra residuo y pide recolección", pg.evaluate("estadoApp.solicitudes.length") == antes + 1)
        id_sol = pg.evaluate("estadoApp.solicitudes[0].id")
        pg.wait_for_timeout(2500)
        uid_nube = pg.evaluate("authFirebase && authFirebase.currentUser ? authFirebase.currentUser.uid : null")
        chk("Ciudadano: sesión real en Firebase Auth", bool(uid_nube), str(uid_nube))
        if uid_nube:
            doc = admin_get("solicitudes_residuos")
            mias = [d for d in doc if d["fields"].get("solicitudId", {}).get("stringValue") == id_sol]
            chk("Nube: la solicitud llegó a Firestore con el uid del vecino",
                len(mias) == 1 and mias[0]["fields"]["usuarioId"]["stringValue"] == uid_nube)
        chk("Header muestra el usuario al ingresar", pg.locator("#header-sesion").is_visible())
        pg.click("button[aria-label='Cerrar sesión']"); pg.wait_for_timeout(800)
        chk("Cerrar sesión: vuelve al ingreso y oculta el header",
            pg.locator("#btn-google-login").is_visible() and not pg.locator("#header-sesion").is_visible()
)
        pg.reload(); pg.wait_for_timeout(1200)
        chk("Tras recargar sigue sin sesión", pg.locator("#btn-google-login").is_visible())
        login(pg, "ciudadano")
        salir(pg)

        # 2. AUTORIDAD
        login(pg, "autoridad"); pg.wait_for_timeout(1000)
        pg.evaluate("estadoApp.solicitudes = estadoApp.solicitudes.filter(x => x.id !== '%s'); guardarEnLocalStorage()" % id_sol)
        pg.reload(wait_until="load"); pg.wait_for_timeout(4000)
        chk("Autoridad: recibe en vivo la solicitud del vecino desde la nube",
            pg.evaluate("estadoApp.solicitudes.some(x => x.id === '%s')" % id_sol))
        vis = lambda: pg.evaluate("['ciudadano','autoridad','recolector'].filter(r=>document.getElementById('vista-'+r).offsetParent!==null)")
        chk("Autoridad: solo se ve su panel (nunca el de ciudadano)", vis() == ["autoridad"], str(vis()))
        pg.reload(wait_until="load"); pg.wait_for_timeout(1500)
        chk("Autoridad: al recargar sigue solo su panel", vis() == ["autoridad"], str(vis()))
        a1 = visible("seccion-kpis-muni"); ir("contenedores"); a2 = visible("panel-iot-card"); ir("rutas"); a3 = visible("btn-optimizar-ruta")
        chk("Autoridad: ve KPIs, planificador y panel de sensores en sus pantallas", a1 and a2 and a3)
        chk("Autoridad: no ve herramientas de cuadrilla ni del vecino", not visible("kpis-cuadrilla") and not visible("lista-disponibilidad-vecino"))
        ir("contenedores")
        chk("Autoridad: tarjetas de telemetría en vivo", pg.locator("#grid-telemetria-iot > div").count() >= 5)
        pg.evaluate("document.querySelector('#panel-iot-card details').open = true")
        pg.click("#btn-forzar-desborde-ui"); pg.wait_for_timeout(1200)
        chk("Autoridad: alerta de desborde visible", "DESBORDE" in pg.inner_text("#grid-telemetria-iot"))
        pg.select_option("#sim-mqtt-select", index=2); pg.click("#btn-preset-78"); pg.click("#btn-publicar-telemetria")
        pg.wait_for_timeout(800)
        chk("Autoridad: calibración actualiza un contenedor", pg.evaluate("estadoApp.ecopuntos[2].capacidad") == 78)
        ir("rutas")
        pg.check(f'.chk-despacho-solicitud[value="{id_sol}"]')
        pg.click("#btn-optimizar-ruta"); pg.wait_for_timeout(1200)
        est = pg.evaluate(f"(()=>{{const s=estadoApp.solicitudes.find(x=>x.id==='{id_sol}');return [s.estado,s.cuadrilla]}})()")
        chk("Autoridad: ruta optimizada (TSP) asignada a cuadrilla", est[0] == "en_camino" and est[1], str(est))
        try:
            pg.wait_for_function("capaRutaPolilinea && capaRutaPolilinea.getLatLngs().length > 8 && !capaRutaPolilinea.options.dashArray", timeout=15000)
            por_calles = True
        except Exception:
            por_calles = False
        chk("Autoridad: la ruta del mapa sigue las calles (OSRM)", por_calles, str(pg.evaluate("capaRutaPolilinea ? capaRutaPolilinea.getLatLngs().length : 0")) + " vértices")
        ir("campanas")
        pg.fill("#input-campana-titulo", "E2E-PRUEBA Jornada de limpieza"); pg.fill("#input-campana-cuerpo", "Sábado en Plaza Cívica")
        pg.evaluate("emitirCampanaMunicipal()"); pg.wait_for_timeout(600)
        chk("Autoridad: emite campaña", pg.evaluate("estadoApp.campanas[0].titulo") == "E2E-PRUEBA Jornada de limpieza")
        ir("resumen")
        chk("Autoridad: tabla de incidentes", pg.locator("#tabla-incidentes-body tr").count() >= 1)
        # Telemetría llegó a la nube
        time.sleep(2)
        doc = json.load(urllib.request.urlopen("https://firestore.googleapis.com/v1/projects/sf-residuos-urbanos-utn/databases/(default)/documents/telemetria_contenedores/ECO-SF-001"))
        v = doc["fields"]["porcentajeLlenado"]
        chk("Nube: desborde forzado llegó a Firestore", float(v.get("doubleValue", v.get("integerValue", 0))) >= 95, str(v))
        salir(pg)

        # 3. CUADRILLA
        login(pg, "cuadrilla"); pg.wait_for_timeout(1000)
        chk("Cuadrilla: ve su resumen del turno y no los controles de sensores", visible("kpis-cuadrilla") and not visible("panel-iot-card") and not visible("btn-forzar-desborde-ui") and not visible("planificador-rutas-card"))
        ir("ruta")
        chk("Cuadrilla: lista de paradas asignadas", pg.locator("#lista-paradas-recolector > *").count() >= 1)
        chk("Cuadrilla: ve la solicitud despachada", id_sol in pg.inner_text("#lista-paradas-recolector"))
        pg.evaluate("abrirModalConfirmar()"); pg.fill("#input-qr-manual", "ECO-SF-001")
        pg.evaluate("validarIdentificadorQR('ECO-SF-001')")
        chk("Cuadrilla: validación de identificador", "Plaza Cívica" in pg.inner_text("#txt-punto-validado-nombre"))
        pg.evaluate("validarIdentificadorQR('XXX-999')")
        chk("Cuadrilla: rechaza identificador inválido", "No encontramos" in pg.inner_text("#txt-punto-validado-nombre"))
        pg.evaluate("abrirModalConfirmar()"); pg.fill("#input-qr-manual", "ECO-SF-001"); pg.evaluate("validarIdentificadorQR('ECO-SF-001')")
        pg.fill("#input-pesaje-recolector", "14.5")
        pg.evaluate("void confirmarRecoleccionEnTerritorio()"); pg.wait_for_timeout(800)
        chk("Cuadrilla: confirma recolección (vacía contenedor)", pg.evaluate("estadoApp.ecopuntos.find(e=>e.id==='ECO-SF-001').capacidad") <= 25)
        chk("Cuadrilla: sin ubicación del teléfono pide confirmación expresa", any("ubicación" in m for m in dialogos), str(dialogos)[:80])
        n = pg.evaluate("estadoApp.incidentes.length")
        pg.evaluate("abrirModalReporteIncidente()")
        pg.fill("#inc-ubicacion", "Av. Urquiza y Roca"); pg.fill("#inc-descripcion", "E2E-PRUEBA contenedor dañado")
        pg.evaluate("document.querySelector('#modal-incidente form').requestSubmit()"); pg.wait_for_timeout(600)
        chk("Cuadrilla: reporta incidente", pg.evaluate("estadoApp.incidentes.length") == n + 1)
        salir(pg)
        login(pg, "ciudadano")
        ir("avisos")
        chk("Ciudadano: recibe la campaña emitida", "E2E-PRUEBA Jornada de limpieza" in pg.inner_text("body"))
        salir(pg)
        chk("El ingreso ya no ofrece correo y contraseña",
            pg.locator("input[type=password], #login-email, #form-login, #form-registro-vecino").count() == 0)
        fuente = (RAIZ / "index.html").read_text(encoding="utf-8")
        chk("El ingreso ofrece solo Google, sin accesos directos", pg.locator("#btn-google-login").is_visible() and pg.locator("[id^=btn-login-rapido-]").count() == 0)
        chk("El código del sitio no contiene contraseñas ni la función de acceso directo",
            not any(x in fuente for x in ("loginRapido", "password:", "signInWithEmailAndPassword")))
        nav.close()
finally:
    if srv: srv.terminate()
    try:
        import admin_nube
        admin_nube.borrar_con_marca("E2E-PRUEBA")
        admin_nube.restaurar_llenado("ECO-SF-001", previo_llenado)
    except Exception as e:
        print("(no se pudo limpiar la nube:", str(e)[:80], ")")

chk("Sin errores JavaScript", not errs, str(errs[:2]))
fallas = [n for n, ok in res if not ok]
print(f"\n{len(res)-len(fallas)}/{len(res)} verificaciones OK")
sys.exit(1 if fallas else 0)
