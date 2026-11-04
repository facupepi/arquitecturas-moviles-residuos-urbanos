"""Verifica que el ingreso con Google esté operativo en producción (sin credenciales: llega hasta la ventana de Google)."""
import sys
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "https://sf-residuos-urbanos-utn.web.app/index.html"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(service_workers="block"); pg = ctx.new_page()
    errores = []
    pg.on("console", lambda m: errores.append(m.text[:160]) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(2500)
    try:
        with ctx.expect_page(timeout=10000) as nueva:
            pg.click("#btn-google-login")
        pop = nueva.value; pop.wait_for_load_state("domcontentloaded", timeout=15000); pop.wait_for_timeout(5000)
        print("VENTANA:", pop.url[:110])
        print("proveedor operativo:", "accounts.google.com" in pop.url or "firebaseapp.com/__/auth/handler" in pop.url)
        pop.close()
    except Exception as e:
        print("sin ventana:", str(e)[:100]); print("aviso:", pg.inner_text("#toast-titulo"), "|", pg.inner_text("#toast-mensaje"))
    print("errores consola:", [e for e in errores if "vibrate" not in e][:3])
