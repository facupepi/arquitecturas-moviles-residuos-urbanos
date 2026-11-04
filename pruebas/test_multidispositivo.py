"""Prueba con tres dispositivos a la vez (vecino, autoridad y cuadrilla) sincronizados por la nube.

Uso: test_multidispositivo.py [URL]   (sin URL levanta la copia local de app/)
"""
import pathlib, subprocess, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import admin_nube
import ayuda_pruebas

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8771/index.html"
srv = None
if len(sys.argv) == 1:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8771", "-d", str(RAIZ)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)

res = []
def chk(nombre, cond, extra=""):
    res.append(bool(cond)); print(("OK   " if cond else "FALLA"), nombre, extra)

def espera(pg, js, t=10000):
    try:
        pg.wait_for_function(js, timeout=t); return True
    except Exception:
        return False

def entrar(ctx, rol):
    pg = ctx.new_page(); pg.goto(URL, wait_until="load"); pg.wait_for_timeout(1500)
    pg.evaluate("([e, c]) => firebase.auth().signInWithEmailAndPassword(e, c)", list(ayuda_pruebas.cuenta(rol)[:2]))
    espera(pg, "!!(authFirebase && authFirebase.currentUser) && !!obtenerSesionActual()", 15000)
    return pg

try:
    with sync_playwright() as p:
        nav = p.chromium.launch()
        mk = lambda: nav.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
        ctxV, ctxA, ctxC = mk(), mk(), mk()
        V = entrar(ctxV, "ciudadano"); A = entrar(ctxA, "autoridad"); C = entrar(ctxC, "recolector")
        for nombre, pg in (("Vecino", V), ("Autoridad", A), ("Cuadrilla", C)):
            chk(f"{nombre}: sesión real en Firebase Auth", pg.evaluate("!!(authFirebase && authFirebase.currentUser)"))
        for pg in (V, A, C): pg.wait_for_timeout(3000)   # carga inicial de las escuchas

        # 1. El vecino pide un retiro y la autoridad lo recibe
        def pedir(texto):
            V.evaluate("abrirModalRegistro()")
            V.check("input[name=tipo_residuo][value=voluminoso]")
            V.evaluate("actualizarSubcategoriasFormulario('voluminoso')"); V.select_option("#reg-subcategoria", index=0)
            V.fill("#reg-cantidad", "2"); V.fill("#reg-direccion", f"Av. Urquiza 100 {texto}"); V.fill("#reg-observaciones", "E2E-PRUEBA")
            V.evaluate("document.getElementById('reg-fecha').value=new Date(Date.now()+864e5).toISOString().slice(0,10)")
            V.evaluate("document.getElementById('form-registro-residuo').requestSubmit()"); V.wait_for_timeout(600)
            return V.evaluate("estadoApp.solicitudes[0].id")
        id1 = pedir("E2E-PRUEBA uno")
        chk("Autoridad recibe la solicitud del vecino en vivo", espera(A, f"estadoApp.solicitudes.some(x => x.id === '{id1}')"))
        chk("Autoridad es avisada de la nueva solicitud", espera(A, "document.getElementById('toast-titulo').innerText.includes('Nueva solicitud')", 4000))

        # 2. La autoridad despacha a la cuadrilla Móvil 03 (por defecto) y la cuadrilla es avisada
        A.wait_for_timeout(500)
        A.evaluate("mostrarPantalla('rutas')"); A.wait_for_timeout(300)
        A.check(f'.chk-despacho-solicitud[value="{id1}"]'); A.click("#btn-optimizar-ruta")
        ok_parada = espera(C, f"document.getElementById('lista-paradas-recolector').innerText.includes('{id1}')")
        if not ok_parada:
            for nom, pg in (("A", A), ("C", C)):
                print("  [diagnóstico", nom, "]", pg.evaluate(f"JSON.stringify((estadoApp.solicitudes.find(x => x.id === '{id1}') || null))"),
                      "| unidad:", pg.evaluate("obtenerSesionActual().unidad"), "| toast:", pg.evaluate("document.getElementById('toast-titulo').innerText"))
        chk("Cuadrilla recibe la parada asignada", ok_parada)
        chk("Cuadrilla es avisada de la nueva parada", espera(C, "document.getElementById('toast-titulo').innerText.includes('Nueva parada')", 4000))
        chk("Cuadrilla ve la ruta trazada en su mapa", C.evaluate("capaRutaCuadrilla !== null"))
        chk("Vecino ve su solicitud en camino y es avisado", espera(V, f"estadoApp.solicitudes.find(x => x.id === '{id1}').estado === 'en_camino'")
            and espera(V, "document.getElementById('toast-titulo').innerText.includes('Novedades')", 4000))

        # 3. Una parada para otra unidad no aparece en la cuadrilla Móvil 03
        id2 = pedir("E2E-PRUEBA dos")
        espera(A, f"estadoApp.solicitudes.some(x => x.id === '{id2}')"); A.wait_for_timeout(500)
        A.evaluate("mostrarPantalla('rutas')"); A.wait_for_timeout(300)
        A.select_option("#select-cuadrilla", index=0)          # Móvil 01
        A.check(f'.chk-despacho-solicitud[value="{id2}"]'); A.click("#btn-optimizar-ruta")
        C.wait_for_timeout(3500)
        chk("La cuadrilla no ve paradas de otra unidad", id2 not in C.inner_text("#lista-paradas-recolector"))

        # 4. La cuadrilla confirma la recolección y todos lo ven
        C.evaluate("abrirModalConfirmar()"); C.fill("#input-qr-manual", id1); C.evaluate(f"validarIdentificadorQR('{id1}')")
        C.fill("#input-pesaje-recolector", "18"); C.evaluate("void confirmarRecoleccionEnTerritorio()")
        chk("Autoridad ve la solicitud recolectada", espera(A, f"estadoApp.solicitudes.find(x => x.id === '{id1}').estado === 'recolectado'"))
        chk("Vecino ve su solicitud recolectada", espera(V, f"estadoApp.solicitudes.find(x => x.id === '{id1}').estado === 'recolectado'"))

        # 5. Campaña de la autoridad llega a vecino y cuadrilla
        A.evaluate("mostrarPantalla('campanas')"); A.wait_for_timeout(300)
        A.fill("#input-campana-titulo", "E2E-PRUEBA Jornada de limpieza"); A.fill("#input-campana-cuerpo", "Sábado en Plaza Cívica")
        A.evaluate("emitirCampanaMunicipal()")
        chk("Vecino recibe la campaña", espera(V, "estadoApp.campanas.some(c => c.titulo.includes('E2E-PRUEBA'))"))
        chk("Vecino es avisado de la campaña", espera(V, "document.getElementById('toast-titulo').innerText.includes('E2E-PRUEBA')", 4000))
        chk("Cuadrilla recibe la campaña", espera(C, "estadoApp.campanas.some(c => c.titulo.includes('E2E-PRUEBA'))"))

        # 6. Incidente de la cuadrilla llega a la autoridad; al resolverlo, la cuadrilla lo ve resuelto
        C.evaluate("abrirModalReporteIncidente()"); C.fill("#inc-ubicacion", "Av. Cervantes E2E-PRUEBA"); C.fill("#inc-descripcion", "E2E-PRUEBA contenedor roto")
        C.evaluate("document.querySelector('#modal-incidente form').requestSubmit()"); C.wait_for_timeout(500)
        idi = C.evaluate("estadoApp.incidentes[0].id")
        chk("Autoridad recibe el incidente de la cuadrilla", espera(A, f"estadoApp.incidentes.some(i => i.id === '{idi}')"))
        chk("Autoridad es avisada del incidente", espera(A, "document.getElementById('toast-titulo').innerText.includes('incidente')", 4000))
        A.evaluate(f"resolverIncidente('{idi}')")
        chk("Cuadrilla ve el incidente resuelto", espera(C, f"estadoApp.incidentes.find(i => i.id === '{idi}').estado === 'resuelto'"))
        nav.close()
finally:
    if srv: srv.terminate()
    try:
        print("limpieza de la nube:", admin_nube.borrar_con_marca("E2E-PRUEBA"), "documentos")
    except Exception as e:
        print("(no se pudo limpiar la nube:", str(e)[:80], ")")

print(f"\n{sum(res)}/{len(res)} verificaciones OK")
sys.exit(0 if all(res) else 1)
