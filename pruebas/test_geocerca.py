"""Valida la geocerca de 35 m de la cuadrilla. Uso: test_geocerca.py [URL]"""
import pathlib, subprocess, sys, time
from playwright.sync_api import sync_playwright
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ayuda_pruebas, admin_nube
RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8773/index.html"
srv = None
if len(sys.argv) == 1:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8773", "-d", str(RAIZ)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
res = []
def chk(n, c, e=""): res.append(bool(c)); print("OK   " if c else "FALLA", n, e)

def caso(nav, lat, lng, aceptar):
    admin_nube.restaurar_llenado("ECO-SF-001", 90)   # en la nube también: si no, la lectura en vivo pisa el valor local
    ctx =nav.new_context(geolocation={"latitude": lat, "longitude": lng}, permissions=["geolocation"], service_workers="block")
    pg = ctx.new_page(); dialogos = []
    pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept() if aceptar else d.dismiss()))
    pg.goto(URL); pg.wait_for_timeout(1500)
    ayuda_pruebas.ingresar(pg, "recolector", 2000)
    pg.evaluate("estadoApp.ecopuntos.find(x => x.id === 'ECO-SF-001').capacidad = 90")  # cada caso parte de un contenedor lleno
    pg.evaluate("abrirModalConfirmar()"); pg.fill("#input-qr-manual", "ECO-SF-001"); pg.evaluate("validarIdentificadorQR('ECO-SF-001')")
    pg.fill("#input-pesaje-recolector", "10"); pg.evaluate("void confirmarRecoleccionEnTerritorio()"); pg.wait_for_timeout(1500)
    r = pg.evaluate("(() => { const e = estadoApp.ecopuntos.find(x => x.id === 'ECO-SF-001'); return [e.capacidad, e.ultimaGeocerca || null] })()")
    ctx.close(); return r, dialogos

previo = admin_nube.llenado("ECO-SF-001")
try:
    with sync_playwright() as p:
        nav = p.chromium.launch()
        r, d = caso(nav, -31.42881, -62.08251, False)
        chk("Dentro de 35 m: se confirma sin avisos", r == [10, "dentro"] and not d, f"{r} {d}")
        r, d = caso(nav, -31.4000, -62.0000, False)
        chk("A kilómetros del punto y se rechaza: no se confirma", r == [90, None] and len(d) == 1, f"{r} {d}")
        r, d = caso(nav, -31.4000, -62.0000, True)
        chk("A kilómetros del punto y se acepta: queda registrada fuera de la geocerca", r == [10, "fuera"], f"{r}")
        nav.close()
finally:
    admin_nube.restaurar_llenado("ECO-SF-001", previo)
    if srv: srv.terminate()
print(f"\n{sum(res)}/{len(res)} verificaciones OK"); sys.exit(0 if all(res) else 1)
