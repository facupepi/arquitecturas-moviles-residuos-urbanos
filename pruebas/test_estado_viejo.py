"""El ingreso debe aparecer aunque el navegador guarde datos viejos o rotos de versiones anteriores. Uso: test_estado_viejo.py [URL]"""
import pathlib, subprocess, sys, time
from playwright.sync_api import sync_playwright
RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
URL = ARGS[0] if ARGS else "http://localhost:8811/index.html"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8811", "-d", str(RAIZ)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if not ARGS else None
time.sleep(1); res = []
try:
    with sync_playwright() as p:
        nav = p.chromium.launch()
        casos = {
            "estado V5 incompleto": ("SF_RESIDUOS_STATE_V5", '{"ecopuntos":[{"id":"ECO-SF-004","coords":[-31.4205,-62.111]}],"usuariosRegistrados":[{"password":"x"}]}'),
            "estado V8 roto": ("SF_RESIDUOS_STATE_V8", '{"ecopuntos":[{"id":"ECO-SF-004","coords":[-31.4205,-62.111]}]}'),
            "sesión local sin usuario en la nube": ("SF_RESIDUOS_AUTH_SESSION_V2", '{"nombre":"X","email":"x","rol":"autoridad","expiracion":9999999999999}'),
        }
        for nombre, (clave, valor) in casos.items():
            pg = nav.new_context(service_workers="block").new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(URL); pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [clave, valor]); pg.reload(); pg.wait_for_timeout(4000)
            ok = pg.locator("#btn-google-login").is_visible()
            res.append(ok); print("OK   " if ok else "FALLA", "El ingreso aparece con", nombre, errs[:1])
        nav.close()
finally:
    if srv: srv.terminate()
print(f"\n{sum(res)}/{len(res)} verificaciones OK"); sys.exit(0 if all(res) else 1)
