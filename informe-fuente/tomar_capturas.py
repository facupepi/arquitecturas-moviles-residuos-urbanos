import os
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pruebas'))
import ayuda_pruebas

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_html = os.path.abspath(os.path.join(base_dir, "..", "app", "index.html"))
    out_dir = os.path.join(base_dir, "capturas")
    os.makedirs(out_dir, exist_ok=True)
    
    import subprocess, time
    servidor = subprocess.Popen([sys.executable, "-m", "http.server", "8797", "-d", os.path.dirname(app_html)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    file_url = "http://localhost:8797/index.html"  # Firebase Auth necesita http(s), no file://
    print(f"Abriendo: {file_url}")
    
    with sync_playwright() as p:
        viewport = {"width": 412, "height": 892}
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=viewport,
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()
        page.goto(file_url, wait_until="load")
        page.wait_for_timeout(2000)
        
        # 0. Pantalla de Ingreso y Autenticación Formal
        page.evaluate("cerrarSesion()")
        page.wait_for_timeout(600)
        p0 = os.path.join(out_dir, "cap0_ingreso_auth.png")
        page.evaluate("cerrarToast()"); page.wait_for_timeout(500)
        page.screenshot(path=p0)
        print("Guardada cap0:", p0)

        # Ingreso como vecino
        ayuda_pruebas.ingresar(page, "ciudadano", 2500)
        
        # 1. Vista Ciudadano (Portal Principal)
        page.evaluate("cambiarRol('ciudadano', true)")
        # dos pedidos del vecino, solo en esta página, para mostrar el seguimiento
        page.evaluate("""() => {
            const uid = firebase.auth().currentUser.uid;
            estadoApp.solicitudes.unshift(
              { id: 'SOL-SF-118', usuario: 'Vecino', usuarioId: uid, tipo: 'voluminoso', subcategoria: 'Muebles y colchones', cantidad: '1 colchón', direccion: 'Bv. 25 de Mayo 1420', coords: [-31.4262, -62.0868], estado: 'pendiente', cuadrilla: null, fecha: 'Próximo turno', observaciones: 'En la vereda desde las 18 h' },
              { id: 'SOL-SF-112', usuario: 'Vecino', usuarioId: uid, tipo: 'reciclable', subcategoria: 'Papel y cartón', cantidad: '3 cajas', direccion: 'Bv. 25 de Mayo 1420', coords: [-31.4262, -62.0868], estado: 'en_camino', cuadrilla: 'Cuadrilla Especial - Móvil 03', fecha: 'Hoy', observaciones: '' });
            renderizarTodo();
        }""")
        page.wait_for_timeout(600)
        p1 = os.path.join(out_dir, "cap1_portal_ciudadano.png")
        page.evaluate("cerrarToast()"); page.wait_for_timeout(500)
        page.screenshot(path=p1)
        print("Guardada cap1:", p1)
        
        # 2. Vista Ciudadano Mapa de Ecopuntos
        page.evaluate("mostrarPantalla('mapa')")
        page.wait_for_timeout(2500) # tiempo para renderizar teselas Esri
        page.evaluate("capasPuntos[0].openPopup()")
        page.wait_for_timeout(1500)
        p2 = os.path.join(out_dir, "cap2_mapa_ecopuntos.png")
        page.evaluate("cerrarToast()"); page.wait_for_timeout(500)
        page.screenshot(path=p2)
        print("Guardada cap2:", p2)
        
        # 3. Vista Panel de Autoridades (Mando Municipal y Despacho TSP)
        ayuda_pruebas.ingresar(page, "autoridad", 2500)
        page.evaluate("mostrarPantalla('rutas')")
        page.wait_for_timeout(2500)
        p3 = os.path.join(out_dir, "cap3_panel_autoridades.png")
        page.evaluate("cerrarToast()"); page.wait_for_timeout(500)
        page.screenshot(path=p3)
        print("Guardada cap3:", p3)
        
        # 4. Vista Recolector (Hoja de Ruta, Scanner y Registro)
        ayuda_pruebas.ingresar(page, "recolector", 2500)
        page.evaluate("mostrarPantalla('ruta')")
        page.wait_for_timeout(2500)
        p4 = os.path.join(out_dir, "cap4_app_recolector_qr.png")
        page.evaluate("cerrarToast()"); page.wait_for_timeout(500)
        page.screenshot(path=p4)
        print("Guardada cap4:", p4)
        
        # 5. Panel municipal en pantalla de escritorio (menú lateral)
        ctx2 = browser.new_context(viewport={"width": 1280, "height": 600}, device_scale_factor=1.5)
        pg2 = ctx2.new_page()
        pg2.goto(file_url, wait_until="load"); pg2.wait_for_timeout(2000)
        ayuda_pruebas.ingresar(pg2, "autoridad", 3500)
        pg2.evaluate("mostrarPantalla('rutas')"); pg2.wait_for_timeout(2500)
        pg2.evaluate("cerrarToast()"); pg2.wait_for_timeout(500)
        p5 = os.path.join(out_dir, "cap5_panel_escritorio.png")
        pg2.screenshot(path=p5)
        print("Guardada cap5:", p5)

        browser.close()
        servidor.terminate()
        print("Todas las capturas se generaron correctamente.")

if __name__ == "__main__":
    main()
