# -*- coding: utf-8 -*-
"""Generador de diagramas vectoriales de alta definición para el Trabajo Práctico de Gestión de Residuos Urbanos.
Cátedra: Arquitecturas Móviles - UTN Facultad Regional San Francisco (UTN FRSFCO).
Docente: Ing. Juan Pablo Bono.
Autores: Facundo Pepino y Mauricio Truchet.
"""
import os
import math
import fitz  # PyMuPDF

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'diagramas')
os.makedirs(SALIDA, exist_ok=True)


def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


# Paleta institucional del trabajo (armónica con TP2, TP3, TP5 y Sistema de Puntos)
VERDE = hx('#12664a')
VERDE_FONDO = hx('#eaf4ef')
AZUL = hx('#1b4f72')
AZUL_FONDO = hx('#ebf5fb')
NARANJA = hx('#b94700')
NARANJA_FONDO = hx('#fff4e6')
PURPURA = hx('#6c3483')
PURPURA_FONDO = hx('#f4ecf7')
CYAN = hx('#0e6251')
CYAN_FONDO = hx('#e8f8f5')
GRIS_BORDE = hx('#c8d6cf')
GRIS_COLUMNA = hx('#f8faf9')
TINTA = hx('#0f1a14')
TEXTO = hx('#2c3e35')
SUAVE = hx('#556960')
CHIP = hx('#ecf2ef')
BLANCO = (1.0, 1.0, 1.0)
DISCONTINUA = '[4 2.5] 0'

F_REG = 'helv'
F_NEG = 'hebo'
F_MONO = 'cour'


def largo(txt, fnt=F_REG, sz=9.0):
    return fitz.get_text_length(txt, fontname=fnt, fontsize=sz)


def partir(txt, fnt, sz, max_w):
    palabras = txt.split()
    lineas = []
    actual = []
    for p in palabras:
        prueba = ' '.join(actual + [p])
        if largo(prueba, fnt, sz) <= max_w:
            actual.append(p)
        else:
            if actual:
                lineas.append(' '.join(actual))
            actual = [p]
    if actual:
        lineas.append(' '.join(actual))
    return lineas


class Lienzo:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.doc = fitz.open()
        self.pag = self.doc.new_page(width=w, height=h)

    def rect(self, x, y, w, h, relleno=None, borde=None, ancho=1.0, radio=3.0, discontinua=False):
        r = fitz.Rect(x, y, x + w, y + h)
        min_side = min(w, h)
        rad_val = min(0.5, radio / min_side) if (radio and min_side > 0) else None
        dashes = DISCONTINUA if discontinua else None
        self.pag.draw_rect(r, color=borde, fill=relleno, width=ancho if borde else 0,
                           radius=rad_val, dashes=dashes)

    def texto(self, x, y, txt, fnt=F_REG, sz=9.0, col=TEXTO):
        self.pag.insert_text(fitz.Point(x, y), txt, fontname=fnt, fontsize=sz, color=col)

    def texto_centrado(self, cx, y, txt, fnt=F_NEG, sz=9.0, col=TEXTO):
        w = largo(txt, fnt, sz)
        self.texto(cx - w / 2, y, txt, fnt, sz, col)

    def flecha(self, p1, p2, color=VERDE, rotulo=None, doble=False, discontinua=False, grosor=1.4):
        p1 = fitz.Point(*p1)
        p2 = fitz.Point(*p2)
        dashes = DISCONTINUA if discontinua else None
        self.pag.draw_line(p1, p2, color=color, width=grosor, lineCap=0 if discontinua else 1, dashes=dashes)
        # Punta en p2
        ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
        for s in (-1, 1):
            q = fitz.Point(p2.x - 7.5 * math.cos(ang + s * math.radians(26)),
                           p2.y - 7.5 * math.sin(ang + s * math.radians(26)))
            self.pag.draw_line(p2, q, color=color, width=grosor, lineCap=1)
        if doble:
            ang_rev = math.atan2(p1.y - p2.y, p1.x - p2.x)
            for s in (-1, 1):
                q = fitz.Point(p1.x - 7.5 * math.cos(ang_rev + s * math.radians(26)),
                               p1.y - 7.5 * math.sin(ang_rev + s * math.radians(26)))
                self.pag.draw_line(p1, q, color=color, width=grosor, lineCap=1)
        if rotulo:
            lines = rotulo.split('\n')
            cx, cy = (p1.x + p2.x) / 2, (p1.y + p2.y) / 2
            max_w = max(largo(l, F_NEG, 8.0) for l in lines)
            pad_x, pad_y = 5, 2.5
            tot_h = len(lines) * 9.5 + pad_y * 2
            rect_rot = fitz.Rect(cx - max_w / 2 - pad_x, cy - tot_h / 2,
                                 cx + max_w / 2 + pad_x, cy + tot_h / 2)
            self.pag.draw_rect(rect_rot, fill=BLANCO, color=color, width=0.7, radius=0.2)
            for i, l in enumerate(lines):
                lw = largo(l, F_NEG, 8.0)
                ty = cy - tot_h / 2 + pad_y + (i + 1) * 9.0 - 0.5
                self.texto(cx - lw / 2, ty, l, F_NEG, 8.0, color)

    def icono(self, nombre, x, y, color):
        """Dibuja un icono vectorial con primitivas geométricas de PyMuPDF."""
        p = self.pag
        g = 1.15

        def L(a, b, w=g):
            p.draw_line(fitz.Point(x + a[0], y + a[1]), fitz.Point(x + b[0], y + b[1]),
                        color=color, width=w)

        def R(a, b, w=g, rad=0.2, fill=None):
            p.draw_rect(fitz.Rect(x + a[0], y + a[1], x + b[0], y + b[1]), color=color,
                        width=w, radius=rad or None, fill=fill)

        def C(cx, cy, r, w=g, fill=None):
            p.draw_circle(fitz.Point(x + cx, y + cy), r, color=color, width=w, fill=fill)

        def O(a, b, w=g):
            p.draw_oval(fitz.Rect(x + a[0], y + a[1], x + b[0], y + b[1]), color=color, width=w)

        def P(pts, w=g):
            for a, b in zip(pts, pts[1:]):
                L(a, b, w)

        if nombre == 'telefono':
            R((2.5, 0), (11.5, 14), rad=0.25)
            L((5.5, 11.5), (8.5, 11.5), 1.0)
            C(7, 2, 0.8, 1.0, color)
        elif nombre == 'escudo':
            P([(7, 0), (13, 2.5), (13, 7.5), (7, 14), (1, 7.5), (1, 2.5), (7, 0)])
            L((4.2, 7.2), (6.2, 9.2), 1.2)
            L((6.2, 9.2), (9.8, 4.8), 1.2)
        elif nombre == 'camion':
            R((0, 3), (9, 12), rad=0.1)
            P([(9, 6), (13, 6), (14, 9), (14, 12), (9, 12)])
            L((10.5, 7.5), (12.5, 7.5), 0.9)
            C(3, 12.5, 1.6, fill=color)
            C(11.5, 12.5, 1.6, fill=color)
        elif nombre == 'base':
            O((0, 0), (14, 4))
            L((0, 2), (0, 12))
            L((14, 2), (14, 12))
            O((0, 5), (14, 9), 1.0)
            O((0, 10), (14, 14))
        elif nombre == 'servidor':
            R((0, 0), (14, 4), rad=0.1)
            R((0, 5), (14, 9), rad=0.1)
            R((0, 10), (14, 14), rad=0.1)
            C(2.5, 2, 0.6, fill=color)
            C(2.5, 7, 0.6, fill=color)
            C(2.5, 12, 0.6, fill=color)
            L((6, 2), (12, 2), 0.9)
            L((6, 7), (12, 7), 0.9)
            L((6, 12), (12, 12), 0.9)
        elif nombre == 'engranaje':
            C(7, 7, 4.0)
            C(7, 7, 1.5, 1.0, fill=color)
            for k in range(8):
                a = k * math.pi / 4
                L((7 + 3.8 * math.cos(a), 7 + 3.8 * math.sin(a)),
                  (7 + 6.2 * math.cos(a), 7 + 6.2 * math.sin(a)), 1.5)
        elif nombre == 'velocimetro':
            pts = []
            for k in range(17):
                a = math.radians(200 + k * 12.5)
                pts.append((7 + 6.2 * math.cos(a), 8.5 + 6.2 * math.sin(a)))
            P(pts)
            L((0.8, 9.5), (13.2, 9.5), 1.0)
            L((7, 8.5), (10.2, 4.2), 1.4)
            C(7, 8.5, 1.2, fill=color)
        elif nombre == 'barras':
            R((0.5, 8.5), (3.8, 14), rad=0.1, fill=color)
            R((5.3, 4.5), (8.6, 14), rad=0.1, fill=color)
            R((10.1, 0.5), (13.4, 14), rad=0.1, fill=color)
        elif nombre == 'nube':
            C(5, 7, 3.2)
            C(8.5, 5.5, 3.8)
            C(11.5, 8, 2.5)
            L((2.5, 10.2), (13.5, 10.2), 1.2)
        elif nombre == 'globo':
            C(7, 7, 6.5)
            O((3.6, 0.5), (10.4, 13.5), 1.0)
            L((0.5, 7), (13.5, 7), 1.0)
        elif nombre == 'enviar':
            P([(0.5, 6.5), (13.5, 0.5), (8.5, 13.5), (6.5, 8.5), (0.5, 6.5)])
            L((6.5, 8.5), (13.5, 0.5), 1.1)
        elif nombre == 'carpeta':
            P([(0, 2), (5, 2), (6.5, 4), (14, 4), (14, 13), (0, 13), (0, 2)])
            L((0, 6), (14, 6), 1.0)
        elif nombre == 'sensor':
            # Antena y ondas de radio (IoT)
            C(7, 10, 2.0, fill=color)
            L((7, 10), (7, 4), 1.5)
            O((4, 1), (10, 7), 1.0)
            O((1.5, 0), (12.5, 10), 1.0)

    def guardar(self, nombre):
        pdf_path = os.path.join(SALIDA, f"{nombre}.pdf")
        png_path = os.path.join(SALIDA, f"{nombre}.png")
        svg_path = os.path.join(SALIDA, f"{nombre}.svg")
        self.doc.save(pdf_path)
        # Render a PNG en ultra-alta resolución (3.2x zoom para 230+ DPI nítido en Word)
        mat = fitz.Matrix(3.2, 3.2)
        pix = self.pag.get_pixmap(matrix=mat, alpha=False)
        pix.save(png_path)
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(self.pag.get_svg_image())
        print(f"Diagrama generado: {png_path} ({self.w}x{self.h} pt)")


def generar_figura_1():
    """Figura 1: arquitectura del sistema con los componentes reales y su estado de avance."""
    W, H = 740, 560
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)
    GRIS = SUAVE
    ESTADOS = {'IMPLEMENTADO': VERDE, 'PROBADO EN CLÚSTER LOCAL': AZUL, 'CONFIGURADO, SIN EJECUTAR': PURPURA, 'PROPUESTO': GRIS}

    def caja(x, y, w, h, titulo, detalle, estado, color, fondo, icono_nom):
        l.rect(x, y, w, h, relleno=fondo, borde=color, radio=4, ancho=1.1)
        l.icono(icono_nom, x + 8, y + 8, color)
        l.texto(x + 28, y + 18, titulo, F_NEG, 9.2, TINTA)
        for i, lin in enumerate(partir(detalle, F_REG, 8.2, w - 24)):
            l.texto(x + 8, y + 33 + i * 11.0, lin, F_REG, 8.2, TEXTO)
        tag = estado
        tw = largo(tag, F_NEG, 6.2) + 8
        l.rect(x + w - tw - 5, y + h - 15, tw, 11, relleno=ESTADOS[estado], radio=2)
        l.texto_centrado(x + w - tw / 2 - 5, y + h - 7, tag, F_NEG, 6.2, BLANCO)

    def banda(x, y, w, h, titulo, sub, col):
        l.rect(x, y, w, h, relleno=GRIS_COLUMNA, borde=GRIS_BORDE, radio=6)
        l.rect(x, y, w, 32, relleno=col, radio=6)
        l.texto_centrado(x + w / 2, y + 14, titulo, F_NEG, 9.8, BLANCO)
        l.texto_centrado(x + w / 2, y + 26, sub, F_REG, 8.2, BLANCO)

    # --- Parte superior: clientes y servicios en la nube
    izq, der, aw = 12, 428, 300
    banda(izq, 12, aw, 270, "CLIENTES", "Navegador del celular o de la oficina", VERDE)
    banda(der, 12, aw, 270, "SERVICIOS EN LA NUBE", "Firebase (plan gratuito) y mapas abiertos", NARANJA)

    caja(izq + 8, 50, aw - 16, 142, "Aplicación web por rol (PWA)",
         "Vecino, municipio y cuadrilla, cada uno con su tablero. El vecino pide retiros y ve ecopuntos y horarios. El municipio despacha rutas con vecino más cercano y 2-opt y ve los contenedores en vivo. La cuadrilla lee códigos QR, valida la geocerca de 35 m y reporta incidentes. Se instala como aplicación y se adapta a pantallas desde 360 px.",
         'IMPLEMENTADO', VERDE, VERDE_FONDO, 'telefono')
    caja(izq + 8, 198, aw - 16, 76, "Service worker y caché",
         "Permite abrir la app sin conexión y recibe los avisos push con la app cerrada.",
         'IMPLEMENTADO', VERDE, VERDE_FONDO, 'carpeta')

    caja(der + 8, 50, aw - 16, 52, "Firebase Authentication",
         "Ingreso con Google. El rol sale del correo verificado.", 'IMPLEMENTADO', NARANJA, NARANJA_FONDO, 'escudo')
    caja(der + 8, 108, aw - 16, 52, "Cloud Firestore",
         "Datos en tiempo real con reglas de seguridad por rol.", 'IMPLEMENTADO', NARANJA, NARANJA_FONDO, 'base')
    caja(der + 8, 166, aw - 16, 52, "Mapas: Esri y OSRM",
         "Teselas del mapa y rutas por calles.", 'IMPLEMENTADO', NARANJA, NARANJA_FONDO, 'globo')
    caja(der + 8, 224, aw - 16, 50, "Firebase Cloud Messaging",
         "Push hacia el celular aunque la app esté cerrada.", 'IMPLEMENTADO', NARANJA, NARANJA_FONDO, 'enviar')

    # Flechas horizontales con rótulo en el hueco entre bloques (sin cruces)
    x1, x2 = izq + aw, der
    l.flecha((x1 - 8, 76), (x2 + 8, 76), color=NARANJA, rotulo="Ingreso con Google", doble=True)
    l.flecha((x1 - 8, 134), (x2 + 8, 134), color=NARANJA, rotulo="Datos en vivo", doble=True)
    l.flecha((x1 - 8, 176), (x2 + 8, 192), color=NARANJA, rotulo="Mapa y rutas", doble=True, discontinua=True)
    l.flecha((x2 + 8, 249), (x1 - 8, 236), color=NARANJA, rotulo="Aviso push", grosor=1.4)

    # --- Parte inferior: infraestructura contenerizada
    banda(12, 296, 716, 232, "INFRAESTRUCTURA CONTENERIZADA", "Despliegue alternativo en un clúster municipal; la producción actual corre en Firebase Hosting", AZUL)
    bw, bh, gx = 220, 88, 20
    xs = [20, 20 + bw + gx, 20 + 2 * (bw + gx)]
    filas = [338, 434]
    caja(xs[0], filas[0], bw, bh, "Imagen Docker (Nginx)", "Servidor sin privilegios de 29,7 MB con cabeceras de seguridad y chequeo de salud.", 'IMPLEMENTADO', AZUL, AZUL_FONDO, 'servidor')
    caja(xs[1], filas[0], bw, bh, "Kubernetes", "Despliegue de 2 réplicas, servicio interno e ingreso con TLS (el ingreso no se probó).", 'PROBADO EN CLÚSTER LOCAL', AZUL, AZUL_FONDO, 'engranaje')
    caja(xs[2], filas[0], bw, bh, "Autoescalado (HPA)", "De 2 a 10 réplicas con CPU sobre 70 %. Medido: pasó de 2 a 10 en unos 40 s bajo carga.", 'PROBADO EN CLÚSTER LOCAL', AZUL, AZUL_FONDO, 'velocimetro')
    caja(xs[0], filas[1], bw, bh, "Prometheus y Grafana", "Recolección cada 15 s, alertas de errores 5xx y latencia, y tablero de cuatro señales.", 'CONFIGURADO, SIN EJECUTAR', PURPURA, PURPURA_FONDO, 'barras')
    caja(xs[1], filas[1], bw, bh, "Sensores y broker MQTT", "Nodos ultrasónicos con Mosquitto y servicio de ingesta hacia Firestore.", 'PROPUESTO', GRIS, CHIP, 'sensor')
    caja(xs[2], filas[1], bw, bh, "Simulador y emisor push", "Scripts que publican lecturas de contenedores y envían avisos por FCM con credencial de administración.", 'IMPLEMENTADO', VERDE, VERDE_FONDO, 'enviar')

    # Descarga de la app desde la infraestructura hacia el cliente
    l.flecha((izq + aw / 2, 296), (izq + aw / 2, 282), color=AZUL, grosor=1.4)
    l.texto(izq + aw / 2 + 10, 292, "Entrega la app por HTTPS", F_NEG, 7.6, AZUL)

    # Leyenda de estados
    x = 20
    for nombre, col in ESTADOS.items():
        tw = largo(nombre, F_NEG, 6.8) + 10
        l.rect(x, 536, tw, 12, relleno=col, radio=2)
        l.texto_centrado(x + tw / 2, 545, nombre, F_NEG, 6.8, BLANCO)
        x += tw + 10

    l.guardar("fig1_arquitectura_residuos")


def generar_figura_2():
    """Figura 2: Diagrama de Secuencia y Flujo Operativo Integral con IoT y Recolección."""
    W, H = 740, 480
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)

    # 6 Participantes estructurados
    participantes = [
        ("Sensor IoT (ESP32)", 60, CYAN, CYAN_FONDO, 'sensor'),
        ("Broker MQTT / K8s", 185, CYAN, CYAN_FONDO, 'servidor'),
        ("Cloud Firestore", 310, NARANJA, NARANJA_FONDO, 'base'),
        ("Municipio (Panel)", 435, AZUL, AZUL_FONDO, 'escudo'),
        ("Backend TSP", 555, AZUL, AZUL_FONDO, 'engranaje'),
        ("Cuadrilla en Calle", 670, VERDE, VERDE_FONDO, 'camion'),
    ]

    for nombre, cx, col_b, col_f, ico in participantes:
        pw = 104
        # Cabecera
        l.rect(cx - pw / 2, 14, pw, 30, relleno=col_f, borde=col_b, radio=4, ancho=1.2)
        l.icono(ico, cx - pw / 2 + 5, 21, col_b)
        l.texto_centrado(cx + 8, 32, nombre, F_NEG, 8.0, col_b)
        # Línea de vida
        l.pag.draw_line(fitz.Point(cx, 44), fitz.Point(cx, 434), color=GRIS_BORDE, width=0.9, dashes=DISCONTINUA)
        # Pie
        l.rect(cx - pw / 2, 436, pw, 24, relleno=col_f, borde=col_b, radio=3, ancho=1.1)
        l.texto_centrado(cx, 451, nombre, F_NEG, 7.8, col_b)

    # Pasos de Secuencia
    y = 66
    pasos = [
        (60, 185, "1. Publica telemetría: ultrasonido nivel 88%, temp 24°C [MQTT QoS 1]", CYAN, False),
        (185, 310, "2. Worker de ingesta evalúa umbral (>80%) y activa [alerta_desborde: true]", NARANJA, False),
        (310, 435, "3. Evento reactivo onSnapshot() enciende alarma en panel de San Francisco", NARANJA, False),
        (435, 555, "4. Despachador ejecuta optimización de ruta TSP priorizando contenedor crítico", AZUL, False),
        (555, 310, "5. Actualiza orden secuencial de paradas y asigna cuadrilla [en_camino]", AZUL, False),
        (310, 670, "6. Emisión de aviso push FCM al chofer con nueva hoja de ruta optimizada", NARANJA, False),
        (670, 670, "7. Cuadrilla inicia recorrido vehicular hacia el punto verde", VERDE, True),
        (670, 555, "8. Escaneo de código QR en contenedor con la cámara del teléfono móvil", VERDE, False),
        (555, 555, "9. Backend valida firma criptográfica municipal y geocerca (<35m)", AZUL, True),
        (555, 310, "10. Registra pesaje en báscula (kg) y commuta estado a [recolectado]", AZUL, False),
        (310, 435, "11. Cierre automático de alerta en panel municipal y actualización de KPIs", NARANJA, False),
        (60, 185, "12. Sensor IoT detecta vaciado por ultrasonido (nivel 8%) y normaliza tópico", CYAN, False),
    ]

    for p_origen, p_destino, mensaje, color, es_autollamada in pasos:
        if es_autollamada:
            l.rect(p_origen - 5, y - 2, 10, 20, relleno=color, radio=2)
            l.texto(p_origen + 12, y + 11, mensaje, F_NEG, 7.8, color)
            y += 29
        else:
            l.flecha((p_origen, y), (p_destino, y), color=color, grosor=1.3)
            cx = (p_origen + p_destino) / 2
            tw = largo(mensaje, F_REG, 7.8) + 8
            l.rect(cx - tw / 2, y - 9, tw, 12, relleno=BLANCO, radio=2)
            l.texto_centrado(cx, y - 0.5, mensaje, F_REG, 7.8, TINTA)
            y += 31

    l.guardar("fig2_secuencia_residuos")


if __name__ == '__main__':
    print("Compilando diagramas vectoriales con capa IoT y MQTT...")
    generar_figura_1()
    generar_figura_2()
    print("Diagramas generados con éxito en:", SALIDA)
