"""La aplicación abre sin conexión: el service worker guarda el sitio y las bibliotecas externas versionadas.
Uso: test_sin_conexion.py [URL]   (por defecto, el sitio publicado; necesita HTTPS o localhost)"""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://sf-residuos-urbanos-utn.web.app/"
res = []
def chk(n, c, e=""): res.append(bool(c)); print("OK   " if c else "FALLA", n, e)

with sync_playwright() as p:
    nav = p.chromium.launch(); ctx = nav.new_context(); pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=30000)
    pg.reload(); pg.wait_for_timeout(4000)                        # segunda visita: todo queda guardado
    ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(4000)
    chk("Sin red, la aplicación abre y muestra el ingreso", pg.evaluate("document.body.innerText.includes('Continuar con Google')"))
    chk("Sin red, el SDK de Firebase se carga desde el teléfono", pg.evaluate("typeof firebase !== 'undefined'"))
    chk("Sin red, el mapa y los íconos están disponibles", pg.evaluate("typeof L !== 'undefined' && typeof lucide !== 'undefined'"))
    nav.close()
print(f"\n{sum(res)}/{len(res)} verificaciones OK"); sys.exit(0 if all(res) else 1)
