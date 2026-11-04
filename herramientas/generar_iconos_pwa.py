"""Genera los íconos de la app (azul municipal del TP5 con el símbolo de reciclaje de Lucide)."""
import pathlib
from playwright.sync_api import sync_playwright
DEST = pathlib.Path(__file__).resolve().parent.parent / "app/icons"
HTML = """<html><body style='margin:0'><div id=c style='width:{t}px;height:{t}px;background:#0077ae;display:flex;align-items:center;justify-content:center;{r}'>
<i data-lucide='recycle' style='width:{g}px;height:{g}px;color:#fff;stroke-width:1.6'></i></div>
<script src='https://unpkg.com/lucide@0.469.0'></script><script>lucide.createIcons();document.querySelector('svg').setAttribute('stroke-width','1.6')</script></body></html>"""
casos = {"icon-192.png": (192, 0.58, ""), "icon-512.png": (512, 0.58, ""), "icon-maskable.png": (512, 0.42, ""), "apple-touch-icon.png": (180, 0.58, "")}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    for nombre, (t, f, r) in casos.items():
        pg.set_viewport_size({"width": t, "height": t})
        pg.set_content(HTML.format(t=t, g=int(t * f), r=r)); pg.wait_for_timeout(1200)
        pg.locator("#c").screenshot(path=str(DEST / nombre)); print("ok", nombre)
