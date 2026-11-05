"""Mide cuánto acorta el segundo método (2-opt) el recorrido del vecino más cercano.

Ejecuta la función real de la aplicación (resolverTSP) en el navegador con 1.000 conjuntos de paradas
al azar dentro de la ciudad para cada tamaño, con semilla fija para que el resultado se pueda repetir.
Uso: python pruebas/medir_rutas.py   (escribe pruebas/evidencia_rutas.txt)
"""
import pathlib, subprocess, sys, time
from playwright.sync_api import sync_playwright

RAIZ = pathlib.Path(__file__).resolve().parent.parent
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8796", "-d", str(RAIZ / "app")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
MEDIR = """([n, conjuntos, semilla]) => {
  let s = semilla >>> 0;
  const azar = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const base = { id: 'BASE', coords: COORDS_SF };
  let suma = 0, empeora = 0, mejora = 0;
  for (let k = 0; k < conjuntos; k++) {
    const ds = Array.from({ length: n }, (_, i) => ({ id: 'P' + i,
      coords: [-31.4290 + (azar() - .5) * .03, -62.0820 + (azar() - .5) * .04] }));
    const r = resolverTSP(base, ds);
    if (r.distanciaKm > r.distanciaInicialKm + 1e-9) empeora++;
    if (r.distanciaKm < r.distanciaInicialKm - 1e-9) mejora++;
    suma += (r.distanciaInicialKm - r.distanciaKm) / r.distanciaInicialKm;
  }
  return { promedio: 100 * suma / conjuntos, empeora, mejora };
}"""
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.goto("http://localhost:8796/index.html"); pg.wait_for_function("typeof resolverTSP === 'function'")
        lineas = ["Mejora del 2-opt sobre el vecino más cercano (función resolverTSP de app/index.html),",
                  "1.000 conjuntos de paradas al azar por tamaño, semilla 2026:"]
        for n in (5, 8, 12):
            r = pg.evaluate(MEDIR, [n, 1000, 2026])
            lineas.append(f"  {n:2d} paradas: {r['promedio']:.1f} % en promedio; mejoró {r['mejora']} conjuntos y empeoró {r['empeora']}")
        b.close()
finally:
    srv.terminate()
texto = "\n".join(lineas)
print(texto)
(RAIZ / "pruebas/evidencia_rutas.txt").write_text(texto + "\n", encoding="utf-8")
