"""Comprueba que todos los íconos de cada rol se dibujan (ninguno queda sin resolver). Uso: verificar_iconos.py [URL]"""
import pathlib, subprocess, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright
import ayuda_pruebas
RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8793/index.html"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8793", "-d", str(RAIZ)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if len(sys.argv) == 1 else None
time.sleep(1); ok = True
try:
    with sync_playwright() as p:
        nav = p.chromium.launch(); pg = nav.new_context(viewport={"width": 1280, "height": 900}, service_workers="block").new_page()
        errores = []; pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
        pg.goto(URL); pg.wait_for_timeout(1500)
        print("ingreso: sin resolver", pg.evaluate("[...document.querySelectorAll('i[data-lucide]')].map(i=>i.dataset.lucide)"))
        for rol in ("ciudadano", "autoridad", "recolector"):
            ayuda_pruebas.ingresar(pg, rol, 2500)
            pg.evaluate("lucide.createIcons()")
            f = pg.evaluate("[...document.querySelectorAll('i[data-lucide]')].map(i=>i.dataset.lucide)")
            print(rol, "sin resolver:", f); ok &= not f
            pg.evaluate("cerrarSesion()"); pg.wait_for_timeout(600)
        print("errores de consola:", [e for e in errores if "lucide" in e.lower() or "icon" in e.lower()])
        nav.close()
finally:
    if srv: srv.terminate()
sys.exit(0 if ok else 1)
