"""Push con la app cerrada: registra un dispositivo, cierra la página, envía por FCM y comprueba que el
service worker mostró el aviso. Uso: test_push.py [URL]  (sin URL levanta servidor local)."""
import json, pathlib, subprocess, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright
import ayuda_pruebas
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "infraestructura/notificaciones"))
import enviar_push

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "app"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
URL = ARGS[0] if ARGS else "http://localhost:8795/index.html"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8795", "-d", str(RAIZ)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if not ARGS else None
time.sleep(1)
res = []
def chk(n, c, e=""): res.append(bool(c)); print("OK   " if c else "FALLA", n, e)

try:
    with sync_playwright() as p:
        # Chrome rechaza el Push en contextos de incógnito: hace falta un perfil persistente y una ventana real
        import tempfile
        perfil = tempfile.mkdtemp(prefix="perfil_push_")
        ctx = p.chromium.launch_persistent_context(perfil, channel="chrome", headless=False, permissions=["notifications"], ignore_default_args=["--disable-background-networking", "--disable-component-update", "--disable-default-apps", "--disable-extensions"])
        nav = ctx
        pg = ctx.new_page(); pg.on("console", lambda m: print("  [consola]", m.text[:160]) if "Push" in m.text else None); pg.goto(URL); pg.wait_for_timeout(2500)
        ayuda_pruebas.ingresar(pg, "ciudadano", 1500)
        uid = ayuda_pruebas.cuenta("ciudadano")[2]
        pg.evaluate("void registrarPushFCM()")
        try:
            pg.wait_for_function("!!tokenPush", timeout=20000)
        except Exception:
            pass
        token = pg.evaluate("tokenPush")
        chk("El dispositivo obtiene su token de FCM", bool(token), (token or "")[:24])
        if token:
            chk("El token queda registrado en la nube a nombre del usuario", token in enviar_push.dispositivos(uid=uid))
            sw = next((w for w in ctx.service_workers if w.url.endswith("/sw.js")), None)
            chk("El service worker de la app está activo", sw is not None)
            # Se registra lo que el service worker pide mostrar (getNotifications no es fiable en Chrome de escritorio)
            sw.evaluate("""() => { self.__mostradas = []; const orig = self.registration.showNotification.bind(self.registration);
                self.registration.showNotification = (t, o) => { self.__mostradas.push(t + '|' + o.body); return orig(t, o); }; }""")
            time.sleep(8)  # el registro nuevo tarda unos segundos en propagarse hasta el servicio de push
            pg.goto("about:blank")  # app cerrada (la ventana sigue abierta para que Chrome mantenga la conexión de push)
            ok, malos = enviar_push.enviar([token], "E2E-PRUEBA aviso", "Llegó con la app cerrada", tag="e2e")
            chk("FCM acepta el mensaje", ok == 1 and malos == 0, f"{ok}/{malos}")
            mostradas = []
            for _ in range(25):
                mostradas = sw.evaluate("self.__mostradas")
                if mostradas: break
                time.sleep(1)
            chk("El service worker recibe el push y muestra el aviso con la app cerrada", "E2E-PRUEBA aviso|Llegó con la app cerrada" in mostradas, str(mostradas))
            pg2 = pg; pg2.goto(URL); pg2.wait_for_timeout(1500)
            pg2.evaluate("void cerrarSesion()"); pg2.wait_for_timeout(2500)
            chk("Al cerrar sesión el dispositivo deja de estar registrado", token not in enviar_push.dispositivos())
        nav.close()
finally:
    if srv: srv.terminate()
print(f"\n{sum(res)}/{len(res)} verificaciones OK")
sys.exit(0 if res and all(res) else 1)
