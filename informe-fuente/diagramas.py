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
    """Figura 1: arquitectura del sistema."""
    W, H = 740, 480
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)

    def caja(x, y, w, h, titulo, detalle, color, fondo, icono_nom):
        l.rect(x, y, w, h, relleno=fondo, borde=color, radio=4, ancho=1.1)
        l.icono(icono_nom, x + 8, y + 8, color)
        l.texto(x + 28, y + 18, titulo, F_NEG, 9.2, TINTA)
        for i, lin in enumerate(partir(detalle, F_REG, 8.2, w - 24)):
            l.texto(x + 8, y + 33 + i * 11.0, lin, F_REG, 8.2, TEXTO)

    def banda(x, y, w, h, titulo, sub, col):
        l.rect(x, y, w, h, relleno=GRIS_COLUMNA, borde=GRIS_BORDE, radio=6)
        l.rect(x, y, w, 32, relleno=col, radio=6)
        l.texto_centrado(x + w / 2, y + 14, titulo, F_NEG, 9.8, BLANCO)
        l.texto_centrado(x + w / 2, y + 26, sub, F_REG, 8.2, BLANCO)

    izq, der, aw = 12, 428, 300
    banda(izq, 12, aw, 262, "CLIENTES", "Navegador del celular o de la oficina", VERDE)
    banda(der, 12, aw, 262, "SERVICIOS EN LA NUBE", "Firebase y mapas abiertos", NARANJA)

    caja(izq + 8, 50, aw - 16, 138, "Aplicación web por rol",
         "El vecino pide retiros y consulta ecopuntos, horarios y campañas. El municipio ve los contenedores en vivo, planifica rutas y atiende incidentes. La cuadrilla recibe su hoja de ruta, escanea códigos QR, valida su ubicación y reporta problemas en la calle.",
         VERDE, VERDE_FONDO, 'telefono')
    caja(izq + 8, 194, aw - 16, 72, "Service worker y caché",
         "Abre la aplicación sin conexión y recibe los avisos push con la aplicación cerrada.",
         VERDE, VERDE_FONDO, 'carpeta')

    caja(der + 8, 50, aw - 16, 50, "Firebase Authentication", "Ingreso con la cuenta de Google.", NARANJA, NARANJA_FONDO, 'escudo')
    caja(der + 8, 106, aw - 16, 50, "Cloud Firestore", "Datos en tiempo real con reglas de seguridad por rol.", NARANJA, NARANJA_FONDO, 'base')
    caja(der + 8, 162, aw - 16, 50, "Mapas Esri y OSRM", "Mapa de la ciudad y recorridos por las calles.", NARANJA, NARANJA_FONDO, 'globo')
    caja(der + 8, 218, aw - 16, 50, "Firebase Cloud Messaging", "Avisos push a los celulares.", NARANJA, NARANJA_FONDO, 'enviar')

    x1, x2 = izq + aw, der
    l.flecha((x1 - 8, 75), (x2 + 8, 75), color=NARANJA, rotulo="Ingreso", doble=True)
    l.flecha((x1 - 8, 131), (x2 + 8, 131), color=NARANJA, rotulo="Datos en vivo", doble=True)
    l.flecha((x1 - 8, 175), (x2 + 8, 187), color=NARANJA, rotulo="Mapa y rutas", doble=True, discontinua=True)
    l.flecha((x2 + 8, 243), (x1 - 8, 231), color=NARANJA, rotulo="Aviso push")

    banda(12, 292, 716, 176, "INFRAESTRUCTURA PROPIA DEL MUNICIPIO", "Contenedores, orquestación, escalado y monitoreo", AZUL)
    bw, bh, gx = 220, 62, 20
    xs = [20, 20 + bw + gx, 20 + 2 * (bw + gx)]
    filas = [334, 402]
    caja(xs[0], filas[0], bw, bh, "Imagen Docker", "Servidor Nginx liviano que entrega la aplicación, sin privilegios y con control de salud.", AZUL, AZUL_FONDO, 'servidor')
    caja(xs[1], filas[0], bw, bh, "Kubernetes", "Mantiene las réplicas de la aplicación y reparte el tráfico entre ellas.", AZUL, AZUL_FONDO, 'engranaje')
    caja(xs[2], filas[0], bw, bh, "Autoescalado", "Suma réplicas cuando sube la demanda y las retira cuando baja.", AZUL, AZUL_FONDO, 'velocimetro')
    caja(xs[0], filas[1], bw, bh, "Prometheus y Grafana", "Recolectan las métricas de cada réplica, las muestran en un tablero y emiten alertas.", PURPURA, PURPURA_FONDO, 'barras')
    caja(xs[1], filas[1], bw, bh, "Sensores de nivel", "Miden el llenado y la temperatura de los contenedores y los envían por MQTT.", CYAN, CYAN_FONDO, 'sensor')
    caja(xs[2], filas[1], bw, bh, "Emisor de avisos", "Lee los dispositivos registrados y envía los avisos por Firebase Cloud Messaging.", CYAN, CYAN_FONDO, 'enviar')

    l.flecha((izq + aw / 2, 292), (izq + aw / 2, 268), color=AZUL)
    l.guardar("fig1_arquitectura_residuos")


def generar_figura_2():
    """Figura 2: secuencia del circuito de recolección."""
    W, H = 740, 520
    l = Lienzo(W, H)
    l.rect(0, 0, W, H, relleno=BLANCO)
    actores = [("Contenedor", "sensor", CYAN, CYAN_FONDO), ("Vecino", "telefono", VERDE, VERDE_FONDO), ("Nube (Firebase)", "nube", NARANJA, NARANJA_FONDO),
               ("Panel municipal", "escudo", AZUL, AZUL_FONDO), ("Cuadrilla", "camion", VERDE, VERDE_FONDO)]
    sep = 146
    xs = [64 + i * sep for i in range(5)]
    for (nombre, ico, col, fondo), x in zip(actores, xs):
        l.rect(x - 56, 12, 112, 34, relleno=fondo, borde=col, radio=4, ancho=1.1)
        l.icono(ico, x - 50, 22, col)
        l.texto(x - 32, 33, nombre, F_NEG, 8.4, TINTA)
        l.pag.draw_line(fitz.Point(x, 46), fitz.Point(x, H - 14), color=GRIS_BORDE, width=1.0, dashes=DISCONTINUA)

    y0, paso = 76, 40

    def mensaje(n, de, a, texto, col):
        y = y0 + n * paso
        lineas = partir(f"{n + 1}. {texto}", F_REG, 8.2, max(abs(xs[a] - xs[de]) - 14, 110))
        for k, lin in enumerate(reversed(lineas)):
            l.texto_centrado((xs[de] + xs[a]) / 2, y - 5 - k * 10, lin, F_REG, 8.2, TINTA)
        d = 4 if xs[a] > xs[de] else -4
        l.flecha((xs[de] + d, y), (xs[a] - d, y), color=col, grosor=1.4)

    def nota(n, de, texto, col, lado=1, ancho=128):
        y = y0 + n * paso
        lineas = partir(f"{n + 1}. {texto}", F_REG, 8.2, ancho - 12)
        h = len(lineas) * 10.5 + 8
        x = xs[de] + 6 if lado > 0 else xs[de] - 6 - ancho
        l.rect(x, y - h / 2, ancho, h, relleno=BLANCO, borde=col, radio=3, ancho=1.0)
        for k, lin in enumerate(lineas):
            l.texto(x + 6, y - h / 2 + 11 + k * 10.5, lin, F_REG, 8.2, TINTA)

    mensaje(0, 0, 2, "Envía el nivel de llenado y la temperatura", CYAN)
    mensaje(1, 2, 3, "Muestra la alerta de desborde en el panel", NARANJA)
    mensaje(2, 1, 2, "Registra la solicitud de retiro con su ubicación", VERDE)
    mensaje(3, 2, 3, "Avisa la solicitud nueva en tiempo real", NARANJA)
    nota(4, 3, "Calcula la ruta más corta y la traza por las calles", AZUL)
    mensaje(5, 3, 2, "Asigna las paradas a la cuadrilla elegida", AZUL)
    mensaje(6, 2, 4, "Entrega la hoja de ruta y envía el aviso push", NARANJA)
    nota(7, 4, "Llega al punto, escanea el código QR y valida que está a menos de 35 m", VERDE, lado=-1, ancho=150)
    mensaje(8, 4, 2, "Confirma el retiro con el peso recolectado", VERDE)
    mensaje(9, 2, 1, "Avisa al vecino que su solicitud se completó", NARANJA)
    mensaje(10, 2, 3, "Actualiza los indicadores y cierra la alerta", NARANJA)
    l.guardar("fig2_secuencia_residuos")


if __name__ == '__main__':
    print("Compilando diagramas vectoriales con capa IoT y MQTT...")
    generar_figura_1()
    generar_figura_2()
    print("Diagramas generados con éxito en:", SALIDA)
