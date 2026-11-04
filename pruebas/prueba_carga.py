"""Prueba de carga sencilla: N clientes concurrentes durante T segundos contra una URL. Informa p50/p95/p99 y errores."""
import sys, time, threading, urllib.request, statistics
URL = sys.argv[1]; N = int(sys.argv[2]); T = float(sys.argv[3])
lat, err, lock = [], [0], threading.Lock()
fin = time.time() + T
def trabajador():
    while time.time() < fin:
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(URL, timeout=10) as r: r.read(); ok = r.status == 200
        except Exception: ok = False
        dt = (time.perf_counter() - t0) * 1000
        with lock:
            lat.append(dt)
            if not ok: err[0] += 1
hs = [threading.Thread(target=trabajador) for _ in range(N)]
[h.start() for h in hs]; [h.join() for h in hs]
lat.sort(); q = lambda p: lat[min(len(lat) - 1, int(len(lat) * p))]
print(f"clientes={N} duración={T:.0f}s peticiones={len(lat)} ({len(lat)/T:.0f}/s) errores={err[0]} p50={q(.5):.0f}ms p95={q(.95):.0f}ms p99={q(.99):.0f}ms")
