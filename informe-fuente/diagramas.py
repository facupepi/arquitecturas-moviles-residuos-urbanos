# -*- coding: utf-8 -*-
"""Generador de diagramas vectoriales de alta definición para el Trabajo Práctico de Gestión de Residuos Urbanos.
Cátedra: Arquitecturas Móviles - UTN Facultad Regional San Francisco (UTN FRSFCO).
Docente: Ing. Juan Pablo Bono.
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
    """Figura 1: arquitectura del sistema."""
    W, H = 560, 470
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)
    T_TIT, T_TXT = 11.0, 10.0

    def caja(x, y, w, h, titulo, detalle, color, fondo, icono_nom):
        l.rect(x, y, w, h, relleno=fondo, borde=color, radio=4, ancho=1.1)
        l.icono(icono_nom, x + 7, y + 7, color)
        l.texto(x + 26, y + 17, titulo, F_NEG, T_TIT, TINTA)
        lineas = partir(detalle, F_REG, T_TXT, w - 14)
        assert 32 + (len(lineas) - 1) * 12 + 4 <= h, f"no entra el texto de {titulo}"
        for i, lin in enumerate(lineas):
            l.texto(x + 7, y + 32 + i * 12.0, lin, F_REG, T_TXT, TEXTO)

    def banda(x, y, w, h, titulo, col):
        l.rect(x, y, w, h, relleno=GRIS_COLUMNA, borde=GRIS_BORDE, radio=6)
        l.rect(x, y, w, 26, relleno=col, radio=6)
        l.texto_centrado(x + w / 2, y + 17.5, titulo, F_NEG, 11.0, BLANCO)

    def rotulo(cx, cy, txt, col):
        w = largo(txt, F_NEG, 9.6)
        l.pag.draw_rect(fitz.Rect(cx - w / 2 - 4, cy - 7.5, cx + w / 2 + 4, cy + 7.5), fill=BLANCO, color=col, width=0.7, radius=0.2)
        l.texto(cx - w / 2, cy + 3.4, txt, F_NEG, 9.6, col)

    def flecha(p1, p2, col, txt=None, en=None, doble=False, discontinua=False):
        l.flecha(p1, p2, color=col, doble=doble, discontinua=discontinua)
        if txt:
            cx, cy = en or ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            rotulo(cx, cy, txt, col)

    # Clientes y servicios en la nube: las cajas de la nube tienen la misma altura y cada flecha
    # sale del centro de una de ellas
    IZQ, DER, AN = 10, 340, 210
    filas = [42, 86, 130, 174, 218]          # cajas de 38 de alto, separadas 6
    banda(IZQ, 10, AN, 254, "CELULARES Y NAVEGADORES", VERDE)
    banda(DER, 10, AN, 254, "SERVICIOS EN LA NUBE", NARANJA)
    caja(IZQ + 8, 42, AN - 16, 126, "Aplicación web", "Un tablero por perfil.", VERDE, VERDE_FONDO, 'telefono')
    for i, (quien, que) in enumerate((("Vecino", "pide retiros"), ("Municipio", "despacha rutas"), ("Cuadrilla", "confirma paradas"))):
        y = 96 + i * 22
        l.pag.draw_circle(fitz.Point(IZQ + 20, y - 3.5), 2.2, color=VERDE, fill=VERDE)
        l.texto(IZQ + 28, y, quien, F_NEG, T_TXT, TINTA)
        l.texto(IZQ + 28 + largo(quien + " ", F_NEG, T_TXT), y, que, F_REG, T_TXT, TEXTO)
    caja(IZQ + 8, 174, AN - 16, 82, "Service worker", "Abre la aplicación sin señal, guarda las bibliotecas y muestra los avisos con la aplicación cerrada.",
         VERDE, VERDE_FONDO, 'carpeta')
    nube = [("Firebase Hosting", "Publica la aplicación.", 'servidor'),
            ("Authentication", "Ingreso con Google.", 'escudo'),
            ("Cloud Firestore", "Datos en vivo.", 'base'),
            ("Esri y OSRM", "Mapa y recorridos.", 'globo'),
            ("Cloud Messaging", "Avisos push.", 'enviar')]
    for (tit, txt, ico), y in zip(nube, filas):
        caja(DER + 8, y, AN - 16, 38, tit, txt, NARANJA, NARANJA_FONDO, ico)
    xa, xb, xm = IZQ + AN - 8 + 2, DER + 8 - 2, (IZQ + AN + DER) / 2
    flecha((xb, 61), (xa, 61), NARANJA, "Publica", en=(xm, 61))
    flecha((xa, 105), (xb, 105), NARANJA, "Ingreso", doble=True, en=(xm, 105))
    flecha((xa, 149), (xb, 149), NARANJA, "Datos", doble=True, en=(xm, 149))
    flecha((xb, 193), (xa, 160), NARANJA, "Mapa", discontinua=True, en=(xm, 176))
    flecha((xb, 237), (xa, 237), NARANJA, "Avisos", en=(xm, 237))

    # Infraestructura propia del municipio (Kubernetes)
    banda(10, 290, 270, 170, "INFRAESTRUCTURA DEL MUNICIPIO", AZUL)
    caja(18, 324, 116, 58, "Kubernetes", "Reparte el tráfico.", AZUL, AZUL_FONDO, 'engranaje')
    caja(158, 324, 114, 58, "Autoescalado", "De 2 a 10 réplicas.", AZUL, AZUL_FONDO, 'velocimetro')
    caja(18, 404, 254, 48, "Prometheus y Grafana", "Métricas y alertas.", PURPURA, PURPURA_FONDO, 'barras')
    flecha((115, 290), (115, 266), AZUL)
    rotulo(115, 277, "Entrega la aplicación", AZUL)
    flecha((158, 353), (136, 353), AZUL)
    flecha((80, 382), (80, 402), PURPURA)

    # Sensores y mensajería, también en el clúster
    banda(290, 290, 260, 104, "SENSORES Y MENSAJES", CYAN)
    caja(298, 324, 120, 62, "Mosquitto", "Recibe y guarda las lecturas.", CYAN, CYAN_FONDO, 'servidor')
    caja(424, 324, 118, 62, "Emisor", "Envía los avisos push.", CYAN, CYAN_FONDO, 'enviar')
    caja(298, 412, 120, 48, "Sensores", "Miden el llenado.", CYAN, CYAN_FONDO, 'sensor')
    flecha((358, 290), (358, 266), CYAN)
    rotulo(358, 277, "Lecturas", CYAN)
    flecha((483, 290), (483, 266), CYAN)
    rotulo(483, 277, "Avisos", CYAN)
    flecha((358, 410), (358, 388), CYAN)
    rotulo(358, 399, "MQTT cifrado", CYAN)
    l.guardar("fig1_arquitectura_residuos")


def generar_figura_2():
    """Figura 2: secuencia del circuito de recolección."""
    W, H = 600, 548
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)
    T = 11.0
    actores = [("Contenedor", "sensor", CYAN, CYAN_FONDO), ("Vecino", "telefono", VERDE, VERDE_FONDO), ("Firebase", "nube", NARANJA, NARANJA_FONDO),
               ("Municipio", "escudo", AZUL, AZUL_FONDO), ("Cuadrilla", "camion", VERDE, VERDE_FONDO)]
    sep = 120
    xs = [60 + i * sep for i in range(5)]
    for (nombre, ico, col, fondo), x in zip(actores, xs):
        l.rect(x - 54, 10, 108, 34, relleno=fondo, borde=col, radio=4, ancho=1.1)
        l.icono(ico, x - 46, 20, col)
        l.texto(x - 26, 31.5, nombre, F_NEG, T, TINTA)
        l.pag.draw_line(fitz.Point(x, 44), fitz.Point(x, H - 10), color=GRIS_BORDE, width=1.0, dashes=DISCONTINUA)

    y0, paso = 76, 44

    def mensaje(n, de, a, texto, col):
        y = y0 + n * paso
        lineas = partir(f"{n + 1}. {texto}", F_REG, T, max(abs(xs[a] - xs[de]) - 12, 228))
        for k, lin in enumerate(reversed(lineas)):
            cx, w = (xs[de] + xs[a]) / 2, largo(lin, F_REG, T)
            l.pag.draw_rect(fitz.Rect(cx - w / 2 - 3, y - 15 - k * 12.5, cx + w / 2 + 3, y - 2 - k * 12.5), fill=BLANCO, color=None, width=0)
            l.texto_centrado(cx, y - 5 - k * 12.5, lin, F_REG, T, TINTA)
        d = 4 if xs[a] > xs[de] else -4
        l.flecha((xs[de] + d, y), (xs[a] - d, y), color=col, grosor=1.4)

    def nota(n, x, ancho, texto, col):
        y = y0 + n * paso
        lineas = partir(f"{n + 1}. {texto}", F_REG, T, ancho - 12)
        h = len(lineas) * 12.5 + 8
        l.rect(x, y - h / 2, ancho, h, relleno=BLANCO, borde=col, radio=3, ancho=1.0)
        for k, lin in enumerate(lineas):
            l.texto(x + 6, y - h / 2 + 13 + k * 12.5, lin, F_REG, T, TINTA)

    mensaje(0, 0, 2, "Envía el llenado, que la ingesta guarda", CYAN)
    mensaje(1, 2, 3, "Muestra la alerta de desborde", NARANJA)
    mensaje(2, 1, 2, "Registra la solicitud de retiro", VERDE)
    mensaje(3, 2, 3, "Avisa la solicitud nueva al instante", NARANJA)
    nota(4, xs[3] - 86, 172, "Calcula la ruta más corta y la traza por las calles", AZUL)
    mensaje(5, 3, 2, "Asigna las paradas a la cuadrilla", AZUL)
    mensaje(6, 2, 4, "Entrega la hoja de ruta y el aviso push", NARANJA)
    nota(7, xs[4] - 72, 124, "Escanea el código a menos de 35 metros", VERDE)
    mensaje(8, 4, 2, "Confirma el retiro con el peso", VERDE)
    mensaje(9, 2, 1, "Avisa que el retiro se completó", NARANJA)
    mensaje(10, 2, 3, "Actualiza los indicadores", NARANJA)
    l.guardar("fig2_secuencia_residuos")


if __name__ == '__main__':
    print("Compilando diagramas vectoriales con capa IoT y MQTT...")
    generar_figura_1()
    generar_figura_2()
    print("Diagramas generados con éxito en:", SALIDA)
