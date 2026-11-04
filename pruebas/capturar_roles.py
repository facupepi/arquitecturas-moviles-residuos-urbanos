import sys
from playwright.sync_api import sync_playwright
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ayuda_pruebas
URL = sys.argv[1] if len(sys.argv) > 1 else "https://sf-residuos-urbanos-utn.web.app/index.html"
JS = "(r)=>[...document.querySelectorAll('#vista-'+r+' h2, #vista-'+r+' h3, #vista-'+r+' h4')].map(h=>h.innerText.trim().split(String.fromCharCode(10))[0]).filter(t=>t)"
import os; os.makedirs("pruebas/img", exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1280, "height": 900}, service_workers="block"); pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(2000)
    for rol in ["ciudadano", "autoridad", "recolector"]:
        ayuda_pruebas.ingresar(pg, rol, 2500)
        pg.screenshot(path=f"pruebas/img/{rol}.png", full_page=True)
        print(rol, pg.evaluate(JS, rol))
        pg.evaluate("cerrarSesion()"); pg.wait_for_timeout(600)
