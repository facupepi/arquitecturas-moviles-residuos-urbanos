# -*- coding: utf-8 -*-
"""
Generador del informe del TP3 (Arquitecturas Moviles, UTN FRSF).

Arma PepinoFacundo_TruchetMauricio_TP3.docx y su PDF a partir de contenido.md,
partiendo de una COPIA del informe del TP2 (que nunca se modifica) para conservar
plantilla, estilos, portada, encabezado con logo, pie y campo de indice.

Uso:
    python generar_informe.py
    python generar_informe.py --contenido otro.md --salida C:\\ruta\\salida.docx
    python generar_informe.py --capturas C:\\dir1 --capturas C:\\dir2 --diagramas C:\\dir3
    python generar_informe.py --sin-render      (no renderiza las paginas a PNG)

Markdown aceptado en contenido.md:
    # N. TITULO                 -> Titulo 1
    ## N.M. Titulo              -> Titulo 2
    parrafos separados por linea en blanco
    - item                      -> vinetas (las del TP2)
    | a | b |  + |---|---|      -> cuadro; la cantidad de guiones de la fila separadora
                                   fija el ancho relativo de cada columna si difieren
    Epigrafe: texto.            -> epigrafe sin numerar debajo del cuadro (o diagrama)
    [[CAPTURA:a.png|Epigrafe.]] || [[CAPTURA:b.png|Epigrafe.]]  -> par de capturas
    [[DIAGRAMA:vista-general]]  (opcional |Epigrafe. o linea Epigrafe: debajo)
    [[DATO:descripcion]]        -> marcador resaltado en amarillo, para reemplazar
    `codigo`  *cursiva*  **negrita**  __subrayado__
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile

import fitz  # PyMuPDF
import pythoncom
import win32com.client

# --------------------------------------------------------------------------- rutas
AQUI = os.path.dirname(os.path.abspath(__file__))
TP_BASE = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
TP2_DOCX = os.path.join(TP_BASE, 'Guia de Trabajos Practicos', 'TP2', 'PepinoFacundo_TruchetMauricio_TP2.docx')
TP_DIR = os.path.abspath(os.path.join(AQUI, '..'))
SALIDA_DOCX = os.path.join(TP_DIR, 'PepinoFacundo_TruchetMauricio_GestionResiduos.docx')
CAPITULOS_EN_PAGINA_NUEVA = ()
PARRAFOS_EN_PAGINA_NUEVA = ()
CONTENIDO = os.path.join(AQUI, 'contenido.md')
CAPTURAS_DIRS = [os.path.join(AQUI, 'capturas')]
DIAGRAMAS_DIRS = [os.path.join(AQUI, 'diagramas')]

# --------------------------------------------------------------------------- portada
TITULO_PORTADA = 'CASO DE ESTUDIO'
SUBTITULO_PORTADA = 'Web Mobile App Gestión Residuos Urbanos'
DATOS_PORTADA = [
    ('Alumnos:', True), ('Pepino, Facundo', False), ('Truchet, Mauricio', False),
    ('Docentes:', True), ('Ing. Bono, Juan Pablo', False),
    ('Asignatura:', True), ('Arquitecturas Móviles', False),
    ('Ciclo Lectivo:', True), ('2026', False),
]
TITULO_DOC = 'Caso de Estudio — Web Mobile App Gestión Residuos Urbanos (San Francisco)'

EPIGRAFES_DIAGRAMA = {
    'fig1_arquitectura_residuos': 'Arquitectura integral del sistema con separación de responsabilidades y servicios en la nube.',
    'fig2_secuencia_residuos': 'Diagrama de secuencia del circuito de registro, asignación, escaneo y recolección.',
}

# --------------------------------------------------------------------------- formato (medido en el TP2)
CUERPO_SA = 10          # pt despues de cada parrafo (ajuste Plan A)
LISTA_SA = 4.5          # pt despues de cada vineta (w:after=90), la ultima lleva CUERPO_SA
LISTA_IZQ = 21.3        # sangria izquierda de la vineta (426 twips)
LISTA_COLGANTE = 14.2   # sangria francesa (284 twips)
INTERLINEADO = 13.8     # 1,15 lineas (wdLineSpaceMultiple)
H1_SB, H1_SA = 18, 8
H2_SB, H2_SA = 14, 8
EPI_COLOR = 0x595959    # gris de los epigrafes del TP2 (BGR == RGB por ser gris)
EPI_TAM = 9
EPI_SB, EPI_SA = 10, 14
TABLA_GRIS = 15922671   # relleno de la fila de titulos (EFF5F2)
TABLA_TAM = 10
TABLA_CELDA_SA = 2.0
TABLA_PAD_V = 3.0
TABLA_PAD_H = 5.0
MONO = "Consolas"
MONO_TAM = 10
CAPTURA_ALTO_MAX = 385  # pt, alto comun de un par de capturas (el del TP2)
DIAGRAMA_ALTO_MAX = 600
CUERPO_ARRIBA = 151.35  # pt, comienzo real del cuerpo debajo del encabezado del TP2 (medido)
CUERPO_ALTO = 841.7 - 72 - CUERPO_ARRIBA   # hasta el margen inferior (A4, 2,54 cm)
DEPURAR = bool(os.environ.get("TP3_DEPURAR"))
CAPTURA_ALTO_EXPANDIDA = 470  # pt, alto maximo al agrandar una captura para llenar una pagina
ACHIQUE_MAX = 0.35      # una figura se achica hasta 35 % para no dejar media pagina vacia

# constantes de Word
wdStyleNormal, wdStyleHeading1, wdStyleHeading2 = -1, -2, -3
wdAlignLeft, wdAlignCenter = 0, 1
wdLineSpaceSingle, wdLineSpaceMultiple = 0, 5
wdCharacter = 1
wdCellAlignVerticalCenter = 1
wdPreferredWidthPercent, wdPreferredWidthPoints = 2, 3
wdExportFormatPDF = 17
wdLineStyleSingle, wdLineStyleNone = 1, 0
wdLineWidth050pt = 4
wdYellow = 7
wdListApplyToWholeList = 0
wdBulletGallery = 1


# =========================================================================== parser
INLINE_RE = re.compile(r"(\*\*.+?\*\*|__.+?__|`[^`]+`|\[\[DATO:[^\]]+\]\]|(?<![\*\w])\*[^*\s][^*]*?\*(?![\*\w]))")


def parse_inline(texto, base=None):
    """Devuelve [(texto, {'b':bool,'i':bool,'mono':bool,'dato':bool})]."""
    base = dict(base or {})
    out = []
    pos = 0
    for m in INLINE_RE.finditer(texto):
        if m.start() > pos:
            out.append((texto[pos:m.start()], dict(base)))
        tok = m.group(0)
        if tok.startswith("**"):
            out.extend(parse_inline(tok[2:-2], dict(base, b=True)))
        elif tok.startswith("__"):
            out.extend(parse_inline(tok[2:-2], dict(base, u=True)))
        elif tok.startswith("`"):
            out.append((tok[1:-1], dict(base, mono=True)))
        elif tok.startswith("[[DATO:"):
            out.append(("[DATO: " + tok[7:-2].strip() + "]", dict(base, dato=True)))
        else:
            out.extend(parse_inline(tok[1:-1], dict(base, i=True)))
        pos = m.end()
    if pos < len(texto):
        out.append((texto[pos:], dict(base)))
    return out


ESPACIO_ARIAL = 0.278 * TABLA_TAM   # ancho del espacio en Arial


def lineas(anchos_palabras, ancho):
    """Lineas que ocupa una celda al cortar las palabras en el ancho dado (Arial 10)."""
    if not anchos_palabras:
        return 1
    n, x = 1, 0.0
    for w in anchos_palabras:
        if x == 0.0:
            x = w
        elif x + ESPACIO_ARIAL + w <= ancho:
            x += ESPACIO_ARIAL + w
        else:
            n += 1
            x = w
    return n


CAPTURA_RE = re.compile(r"\[\[CAPTURA:([^|\]]+)\|([^\]]*)\]\]")
DIAGRAMA_RE = re.compile(r"\[\[DIAGRAMA:([^|\]]+)(?:\|([^\]]*))?\]\]")
EPI_RE = re.compile(r"^Ep[ií]grafe:\s*(.+)$")


def split_row(linea):
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|") and not linea.endswith("\\|"):
        linea = linea[:-1]
    celdas = re.split(r"(?<!\\)\|", linea)
    return [c.strip().replace("\\|", "|") for c in celdas]


def parse_md(texto):
    lineas = texto.replace("\r\n", "\n").split("\n")
    bloques = []
    i = 0
    n = len(lineas)

    def siguiente_epigrafe(j):
        k = j
        while k < n and not lineas[k].strip():
            k += 1
        if k < n:
            m = EPI_RE.match(lineas[k].strip())
            if m:
                return m.group(1).strip(), k + 1
        return None, j

    while i < n:
        l = lineas[i].rstrip()
        s = l.strip()
        if not s or s.startswith("<!--"):
            i += 1
            continue
        if s.startswith("## "):
            bloques.append(("h2", s[3:].strip())); i += 1; continue
        if s.startswith("# "):
            bloques.append(("h1", s[2:].strip())); i += 1; continue
        if s.startswith("[[CAPTURA:"):
            caps = [(m.group(1).strip(), m.group(2).strip()) for m in CAPTURA_RE.finditer(s)]
            if not caps:
                raise ValueError("Marcador de captura mal formado: " + s)
            # hasta tres capturas en una fila (una fila de tres ocupa menos alto que dos pares);
            # con mas de tres, de a dos
            paso = 3 if len(caps) == 3 else 2
            for k in range(0, len(caps), paso):
                bloques.append(("capturas", caps[k:k + paso]))
            i += 1; continue
        if s.startswith("[[DIAGRAMA:"):
            m = DIAGRAMA_RE.match(s)
            nombre = m.group(1).strip()
            epi = (m.group(2) or "").strip()
            j = i + 1
            if not epi:
                e, j2 = siguiente_epigrafe(j)
                if e:
                    epi, j = e, j2
            if not epi:
                epi = EPIGRAFES_DIAGRAMA.get(nombre, "Diagrama.")
            bloques.append(("diagrama", nombre, epi))
            i = j; continue
        if s.startswith("|"):
            filas = []
            sep = None
            while i < n and lineas[i].strip().startswith("|"):
                celdas = split_row(lineas[i])
                if all(re.fullmatch(r":?-{2,}:?", c) for c in celdas if c):
                    sep = [c.count("-") for c in celdas]
                else:
                    filas.append(celdas)
                i += 1
            epi, i = siguiente_epigrafe(i)
            bloques.append(("tabla", filas, sep, epi))
            continue
        if EPI_RE.match(s):
            print("AVISO: epigrafe suelto ignorado:", s)
            i += 1; continue
        if s.startswith("- "):
            items = []
            while i < n and lineas[i].strip().startswith("- "):
                item = lineas[i].strip()[2:].strip()
                i += 1
                # continuaciones con sangria
                while i < n and lineas[i].startswith("  ") and lineas[i].strip() and not lineas[i].strip().startswith("- "):
                    item += " " + lineas[i].strip(); i += 1
                items.append(item)
            bloques.append(("lista", items))
            continue
        # parrafo
        partes = [s]
        i += 1
        while i < n:
            t = lineas[i].strip()
            if not t or t.startswith(("#", "- ", "|", "[[CAPTURA:", "[[DIAGRAMA:")) or EPI_RE.match(t):
                break
            partes.append(t); i += 1
        bloques.append(("p", " ".join(partes)))
    return bloques


# =========================================================================== imagenes
def buscar(nombre, dirs, extensiones):
    base, ext = os.path.splitext(nombre)
    candidatos = [nombre] if ext else [base + e for e in extensiones]
    for d in dirs:
        for c in candidatos:
            p = os.path.join(d, c)
            if os.path.isfile(p):
                return p
    return None


def placeholder(nombre, ancho, alto, tmpdir):
    """Recuadro gris con el texto 'Captura pendiente: nombre' (PNG)."""
    doc = fitz.open()
    pg = doc.new_page(width=ancho, height=alto)
    r = fitz.Rect(1, 1, ancho - 1, alto - 1)
    pg.draw_rect(r, color=(0.62, 0.62, 0.62), fill=(0.90, 0.90, 0.90), width=1.5, dashes="[6 4] 0")
    txt1 = "Captura pendiente:"
    txt2 = nombre
    fs = 10   # mismo tamano en todos los recuadros (solo se achica si el nombre no entra)
    while fs > 6 and max(fitz.get_text_length(txt1, "helv", fs), fitz.get_text_length(txt2, "helv", fs)) > ancho - 20:
        fs -= 0.5
    for k, t in enumerate((txt1, txt2)):
        w = fitz.get_text_length(t, "helv", fs)
        pg.insert_text(((ancho - w) / 2, alto / 2 - 4 + k * (fs + 6)), t, fontsize=fs, fontname="helv", color=(0.3, 0.3, 0.3))
    pix = pg.get_pixmap(matrix=fitz.Matrix(3, 3))
    seguro = re.sub(r"[^\w.-]", "_", nombre)
    ruta = os.path.join(tmpdir, "pendiente_" + seguro + ".png")
    pix.save(ruta)
    doc.close()
    return ruta


def tam_imagen(ruta):
    if ruta.lower().endswith(".svg"):
        d = fitz.open(ruta)
        r = d[0].rect
        d.close()
        return r.width, r.height
    pix = fitz.Pixmap(ruta)
    return pix.width, pix.height


# =========================================================================== Word
class Generador:
    def __init__(self, doc, capturas_dirs, diagramas_dirs, tmpdir):
        self.doc = doc
        self.capturas_dirs = capturas_dirs
        self.diagramas_dirs = diagramas_dirs
        self.tmpdir = tmpdir
        self.reusar = True        # el ultimo parrafo esta vacio y puede usarse
        self.primer_titulo = True
        self.pendientes = []
        self.datos = 0
        ps = doc.PageSetup
        self.ancho_util = ps.PageWidth - ps.LeftMargin - ps.RightMargin
        self.alto_util = ps.PageHeight - ps.TopMargin - ps.BottomMargin

    # ------------------------------------------------------------ parrafos
    def nuevo_parrafo(self):
        if not self.reusar:
            self.doc.Content.InsertParagraphAfter()
        self.reusar = False
        p = self.doc.Paragraphs.Last
        p.Range.ListFormat.RemoveNumbers()
        p.Style = wdStyleNormal
        p.Format.Reset()
        p.Range.Font.Reset()
        p.Range.HighlightColorIndex = 0
        return p

    def formato_cuerpo(self, p, sa=CUERPO_SA, sb=0, centro=False):
        f = p.Format
        f.Alignment = wdAlignCenter if centro else wdAlignLeft
        f.SpaceBefore = sb
        f.SpaceAfter = sa
        f.LineSpacingRule = wdLineSpaceMultiple
        f.LineSpacing = INTERLINEADO
        f.KeepWithNext = False
        f.KeepTogether = False
        f.LeftIndent = 0
        f.FirstLineIndent = 0

    def escribir(self, rango_inicio, runs, mono_tam=MONO_TAM):
        """Inserta los runs en la posicion dada y aplica formato por tramos."""
        doc = self.doc
        texto = "".join(t for t, _ in runs)
        r = doc.Range(rango_inicio, rango_inicio)
        r.InsertAfter(texto)
        ini = r.Start
        off = 0
        for t, f in runs:
            if not t:
                continue
            if any(f.get(k) for k in ("b", "i", "u", "mono", "dato")):
                rr = doc.Range(ini + off, ini + off + len(t))
                if f.get("b"):
                    rr.Font.Bold = True
                if f.get("i"):
                    rr.Font.Italic = True
                if f.get("u"):
                    rr.Font.Underline = 1
                if f.get("mono"):
                    rr.Font.Name = MONO
                    rr.Font.Size = mono_tam
                if f.get("dato"):
                    rr.HighlightColorIndex = wdYellow
                    self.datos += 1
            off += len(t)
        return ini, ini + len(texto)

    def parrafo(self, texto, sa=CUERPO_SA):
        p = self.nuevo_parrafo()
        self.formato_cuerpo(p, sa=sa)
        if any(texto.startswith(prefix) for prefix in PARRAFOS_EN_PAGINA_NUEVA):
            p.Format.PageBreakBefore = True
        self.escribir(p.Range.Start, parse_inline(texto))
        return p

    def titulo(self, texto, nivel):
        p = self.nuevo_parrafo()
        p.Style = wdStyleHeading1 if nivel == 1 else wdStyleHeading2
        f = p.Format
        f.Alignment = wdAlignLeft
        f.SpaceBefore = H1_SB if nivel == 1 else H2_SB
        f.SpaceAfter = H1_SA if nivel == 1 else H2_SA
        if self.primer_titulo:
            f.PageBreakBefore = True     # el cuerpo empieza en la pagina siguiente al indice
            self.primer_titulo = False
        elif nivel == 1 and texto.startswith(CAPITULOS_EN_PAGINA_NUEVA):
            f.PageBreakBefore = True
        self.escribir(p.Range.Start, parse_inline(texto))
        return p

    def lista(self, items, plantilla):
        # Paragraphs.Last es una referencia dinamica: se guardan posiciones, no objetos
        inicio = None
        for k, it in enumerate(items):
            p = self.nuevo_parrafo()
            self.formato_cuerpo(p, sa=LISTA_SA if k < len(items) - 1 else CUERPO_SA)
            if inicio is None:
                inicio = p.Range.Start
            self.escribir(p.Range.Start, parse_inline(it))
        rng = self.doc.Range(inicio, self.doc.Paragraphs.Last.Range.End)
        ps = [rng.Paragraphs(k + 1) for k in range(rng.Paragraphs.Count)]
        if plantilla is not None:
            rng.ListFormat.ApplyListTemplateWithLevel(ListTemplate=plantilla, ContinuePreviousList=False,
                                                      ApplyTo=wdListApplyToWholeList, DefaultListBehavior=2)
        else:
            rng.ListFormat.ApplyBulletDefault()
        # Word pasa las vinetas al estilo "Parrafo de lista"; en el TP2 son estilo Normal
        for p in ps:
            if p.Style.NameLocal not in ("Normal",):
                p.Style = wdStyleNormal
        if rng.ListFormat.ListType == 0 or any(p.Range.ListFormat.ListType == 0 for p in ps):
            if plantilla is not None:
                rng.ListFormat.ApplyListTemplateWithLevel(ListTemplate=plantilla, ContinuePreviousList=False,
                                                          ApplyTo=wdListApplyToWholeList, DefaultListBehavior=2)
            else:
                rng.ListFormat.ApplyBulletDefault()
        for k, p in enumerate(ps):
            f = p.Format
            f.Alignment = wdAlignLeft
            f.LineSpacingRule = wdLineSpaceMultiple
            f.LineSpacing = INTERLINEADO
            f.LeftIndent = LISTA_IZQ
            f.FirstLineIndent = -LISTA_COLGANTE
            f.SpaceAfter = LISTA_SA if k < len(ps) - 1 else CUERPO_SA
            f.SpaceBefore = 0
        return ps

    def epigrafe(self, texto, sb=EPI_SB, sa=EPI_SA, p=None):
        if p is None:
            p = self.nuevo_parrafo()
            self.formato_cuerpo(p, sa=sa, sb=sb, centro=True)
        else:
            f = p.Format
            f.Alignment = wdAlignCenter
            f.SpaceBefore = sb
            f.SpaceAfter = sa
            f.KeepWithNext = False
        a, b = self.escribir(p.Range.Start, parse_inline(texto))
        rr = self.doc.Range(a, b)
        rr.Font.Size = EPI_TAM
        rr.Font.Color = EPI_COLOR
        # el monoespaciado de un epigrafe tambien va a 9 pt
        return p

    # ------------------------------------------------------------ cuadros
    def anchos(self, filas, sep, ncols):
        """Porcentaje del ancho para cada columna. Ninguna columna queda mas angosta que
        su palabra mas larga (asi no se corta una palabra); el resto se reparte para que
        el cuadro quede lo mas bajo posible (menos lineas en total) y lo que sobre, segun
        los guiones de la fila separadora (si difieren 1,5 veces) o el largo del texto."""
        util = self.ancho_util
        palabras = []
        for c in range(ncols):
            mx = 0.0
            for i, f in enumerate(filas):
                for t, fm in parse_inline(f[c] if c < len(f) else ""):
                    for pal in re.split(r"[\s]+", t):
                        if not pal:
                            continue
                        if fm.get("mono"):          # Consolas: 0,55 em por caracter
                            w = len(pal) * 0.55 * TABLA_TAM
                        else:                       # Arial mide igual que Helvetica
                            fuente = "hebo" if (i == 0 or fm.get("b")) else "helv"
                            w = fitz.get_text_length(pal, fuente, TABLA_TAM)
                        mx = max(mx, w)
            palabras.append(mx)
        # con muchas columnas se achica el margen interno lateral antes de cortar palabras
        self.pad_tabla = TABLA_PAD_H
        for pad in (TABLA_PAD_H, 4.0, 2.5):
            self.pad_tabla = pad
            minimos = [min(100.0, (mx + 2 * pad + 3) * 100.0 / util) for mx in palabras]
            if sum(minimos) <= 100.0:
                break
        if sum(minimos) > 100.0:
            # no entra ninguna palabra completa en todas: se reparte en proporcion
            minimos = [m * 100.0 / sum(minimos) for m in minimos]
            print("AVISO: cuadro muy ancho, alguna palabra larga puede cortarse:", filas[0])
        # pesos para repartir lo que sobra una vez minimizada la altura: los guiones de
        # la fila separadora solo cuentan si marcan una diferencia clara (1,5 veces)
        if sep and len(sep) >= ncols and max(sep[:ncols]) >= 1.5 * max(1, min(sep[:ncols])):
            pesos = [float(x) for x in sep[:ncols]]
        else:
            pesos = []
            for c in range(ncols):
                largos = [len(re.sub(r"[`*]", "", f[c])) if c < len(f) else 0 for f in filas]
                mx = min(max(largos), 70)
                prom = sum(largos) / len(largos)
                pesos.append(max(6.0, 0.45 * mx + 0.55 * prom))
        # se reparte el ancho libre de a 0,5 % a la columna que mas lineas ahorra por punto
        # de ancho: el cuadro queda lo mas bajo posible y sin columnas angostas que obliguen
        # a partir cada celda en muchas lineas
        tokens = [[self._tokens(f[c] if c < len(f) else "", i == 0) for c in range(ncols)]
                  for i, f in enumerate(filas)]
        pct = list(minimos)
        paso = 0.5

        cache = {}

        def alto(pc):
            tot = 0
            for i, fila in enumerate(tokens):
                m = 0
                for c in range(ncols):
                    k = (i, c, round(pc[c], 3))
                    v = cache.get(k)
                    if v is None:
                        v = cache[k] = lineas(fila[c], pc[c] * util / 100.0 - 2 * self.pad_tabla - 1)
                    m = max(m, v)
                tot += m
            return tot

        actual = alto(pct)
        libre = 100.0 - sum(pct)
        while libre >= paso:
            mejor = None
            for c in range(ncols):
                prueba = list(pct)
                extra = 0.0
                while extra + paso <= libre + 1e-9:
                    extra += paso
                    prueba[c] = pct[c] + extra
                    h = alto(prueba)
                    if h < actual:
                        ganancia = (actual - h) / extra
                        if mejor is None or ganancia > mejor[0] + 1e-9:
                            mejor = (ganancia, c, extra, h)
                        break
            if mejor is None:
                break
            _, c, extra, h = mejor
            pct[c] += extra
            libre -= extra
            actual = h
        if libre > 0:
            tot = sum(pesos) or 1.0
            pct = [pct[c] + libre * pesos[c] / tot for c in range(ncols)]
            actual = alto(pct)
        # busqueda local: pasar ancho de una columna a otra mientras baje la altura total
        # (el reparto voraz puede quedar en un optimo local con una celda muy alta)
        mejoro = True
        while mejoro:
            mejoro = False
            for a in range(ncols):
                for b in range(ncols):
                    if a == b:
                        continue
                    for k in range(1, 31):
                        d = 0.5 * k
                        if pct[a] - d < minimos[a]:
                            break
                        q = list(pct)
                        q[a] -= d
                        q[b] += d
                        h = alto(q)
                        if h < actual:
                            pct, actual, mejoro = q, h, True
                            break
        self.alto_tabla_lineas = actual
        return pct

    @staticmethod
    def _tokens(texto, encabezado):
        """Anchos (pt) de cada palabra de una celda, con la fuente que le corresponde."""
        out = []
        for t, fm in parse_inline(texto, {"b": True} if encabezado else None):
            for pal in t.split():
                if fm.get("mono"):
                    out.append(len(pal) * 0.55 * TABLA_TAM)
                else:
                    out.append(fitz.get_text_length(pal, "hebo" if fm.get("b") else "helv", TABLA_TAM))
        return out

    def tabla(self, filas, sep, epi):
        doc = self.doc
        ncols = max(len(f) for f in filas)
        filas = [f + [""] * (ncols - len(f)) for f in filas]
        nf = len(filas)
        p = self.nuevo_parrafo()
        self.formato_cuerpo(p)
        t = doc.Tables.Add(p.Range, nf, ncols, 0, 0)
        try:
            t.Style = "Tabla normal"
        except Exception:
            pass
        t.Rows.Alignment = wdAlignLeft
        t.TopPadding = TABLA_PAD_V
        t.BottomPadding = TABLA_PAD_V
        t.LeftPadding = TABLA_PAD_H
        t.RightPadding = TABLA_PAD_H
        t.Spacing = 0
        t.AllowAutoFit = False
        t.PreferredWidthType = wdPreferredWidthPercent
        t.PreferredWidth = 100
        for b in (-1, -2, -3, -4, -5, -6):  # top, left, bottom, right, insideH, insideV
            br = t.Borders(b)
            br.LineStyle = wdLineStyleSingle
            br.LineWidth = wdLineWidth050pt
            br.Color = -16777216  # automatico
        rng = t.Range
        rng.Font.Name = "Arial"
        rng.Font.Size = TABLA_TAM
        pf = rng.ParagraphFormat
        pf.Alignment = wdAlignLeft
        pf.SpaceBefore = 0
        pf.SpaceAfter = TABLA_CELDA_SA
        pf.LineSpacingRule = wdLineSpaceSingle
        pf.KeepWithNext = False
        pf.KeepTogether = False
        pf.LeftIndent = 0
        pf.FirstLineIndent = 0
        rng.Cells.VerticalAlignment = wdCellAlignVerticalCenter
        t.Rows.AllowBreakAcrossPages = False
        t.Rows(1).HeadingFormat = True
        t.Rows(1).Shading.BackgroundPatternColor = TABLA_GRIS
        pct = self.anchos(filas, sep, ncols)
        if self.pad_tabla != TABLA_PAD_H:
            t.LeftPadding = self.pad_tabla
            t.RightPadding = self.pad_tabla
        for c in range(ncols):
            col = t.Columns(c + 1)
            col.PreferredWidthType = wdPreferredWidthPercent
            col.PreferredWidth = pct[c]
        for i, fila in enumerate(filas):
            for c, txt in enumerate(fila):
                celda = t.Cell(i + 1, c + 1)
                runs = parse_inline(txt, {"b": True} if i == 0 else None)
                if any(x for x, _ in runs):
                    self.escribir(celda.Range.Start, runs, mono_tam=TABLA_TAM)
        # si el cuadro tiene pocas filas (<= 7), se mantiene entero en una sola pagina;
        # si es mas largo, se encadenan la de titulos con la primera y la ultima con su epigrafe
        if nf <= 8:
            for row_idx in range(1, nf + 1):
                t.Rows(row_idx).Range.ParagraphFormat.KeepWithNext = True
        else:
            t.Rows(1).Range.ParagraphFormat.KeepWithNext = True
            t.Rows(nf).Range.ParagraphFormat.KeepWithNext = True
        # el parrafo que sigue al cuadro (lo crea Word) se usa para el epigrafe
        self.reusar = True
        if epi:
            self.epigrafe(epi)
        else:
            print("AVISO: cuadro sin epigrafe:", filas[0])
        return t

    # ------------------------------------------------------------ imagenes
    def _ruta_captura(self, nombre):
        ruta = buscar(nombre, self.capturas_dirs, (".png", ".jpg", ".jpeg"))
        if ruta:
            return ruta, False
        self.pendientes.append(nombre)
        return placeholder(nombre, 180, 390, self.tmpdir), True

    def capturas(self, pares):
        doc = self.doc
        rutas = [self._ruta_captura(n)[0] for n, _ in pares]
        ncols = len(pares)
        ancho_tabla = self.ancho_util
        # una captura apaisada sola (escritorio) ocupa todo el ancho; las de celular, media pagina
        apaisada = ncols == 1 and tam_imagen(rutas[0])[0] > tam_imagen(rutas[0])[1]
        ancho_fig = ancho_tabla if (ncols >= 2 or apaisada) else ancho_tabla / 2
        ancho_celda = (ancho_tabla if apaisada else ancho_tabla / max(ncols, 2)) - 2 * TABLA_PAD_H - 4
        # misma altura para las dos, limitada por el ancho de la celda
        alto = CAPTURA_ALTO_MAX
        for r in rutas:
            w, h = tam_imagen(r)
            alto = min(alto, ancho_celda * h / float(w))
        p = self.nuevo_parrafo()
        self.formato_cuerpo(p)
        t = doc.Tables.Add(p.Range, 1, ncols, 0, 0)
        try:
            t.Style = "Tabla normal"
        except Exception:
            pass
        t.Borders.Enable = False
        t.TopPadding = 0
        t.BottomPadding = 0
        t.LeftPadding = TABLA_PAD_H
        t.RightPadding = TABLA_PAD_H
        t.AllowAutoFit = False
        t.PreferredWidthType = wdPreferredWidthPoints
        t.PreferredWidth = ancho_fig
        t.Rows.Alignment = wdAlignCenter
        t.Rows.AllowBreakAcrossPages = False
        for c in range(ncols):
            t.Columns(c + 1).PreferredWidthType = wdPreferredWidthPoints
            t.Columns(c + 1).PreferredWidth = ancho_fig / ncols
        for c, ((nombre, epi), ruta) in enumerate(zip(pares, rutas)):
            celda = t.Cell(1, c + 1)
            r = celda.Range
            r.MoveEnd(wdCharacter, -1)
            r.Text = "\r"          # parrafo 1: imagen; parrafo 2 (fin de celda): epigrafe
            p1 = celda.Range.Paragraphs(1)
            p2 = celda.Range.Paragraphs(2)
            for pp in (p1, p2):
                pp.Style = wdStyleNormal
                pp.Format.Reset()
                pp.Range.Font.Reset()
            f = p1.Format
            f.Alignment = wdAlignCenter
            f.SpaceBefore = 0
            f.SpaceAfter = 4
            f.LineSpacingRule = wdLineSpaceSingle
            # sin "conservar con el siguiente": la fila no se parte, asi que imagen y
            # epigrafe ya van juntos, y la marca encadenaria el cuadro con lo que sigue
            f.KeepWithNext = False
            rr = p1.Range
            rr.Collapse(1)
            pic = doc.InlineShapes.AddPicture(ruta, False, True, rr)
            pic.LockAspectRatio = True
            pic.Height = alto
            pic.Title = "fig-captura"
            pic.AlternativeText = epi
            f2 = p2.Format
            f2.LineSpacingRule = wdLineSpaceMultiple
            f2.LineSpacing = INTERLINEADO
            self.epigrafe(epi, sb=0, sa=EPI_SA, p=p2)
        self.reusar = True
        return t

    def diagrama(self, nombre, epi):
        ruta = buscar(nombre, self.diagramas_dirs, (".svg", ".png"))
        if not ruta:
            self.pendientes.append(nombre)
            ruta = placeholder(nombre, 453, 255, self.tmpdir)
        p = self.nuevo_parrafo()
        self.formato_cuerpo(p, sa=4, centro=True)
        p.Format.LineSpacingRule = wdLineSpaceSingle
        p.Format.KeepWithNext = True
        rr = p.Range
        rr.Collapse(1)
        pic = self.doc.InlineShapes.AddPicture(ruta, False, True, rr)
        pic.LockAspectRatio = True
        pic.Title = "fig-diagrama"
        pic.AlternativeText = epi
        pic.Width = self.ancho_util
        # el encabezado con logo baja el comienzo del cuerpo a unos 151 pt: el tope deja
        # lugar al parrafo que presenta el diagrama y al epigrafe en la misma pagina
        tope = min(DIAGRAMA_ALTO_MAX, CUERPO_ALTO - 90)
        if pic.Height > tope:
            pic.Height = tope
        self.epigrafe(epi)
        return p


# =========================================================================== armado
def preparar_portada(doc):
    hechos = 0
    for k in range(1, 15):
        p = doc.Paragraphs(k)
        txt = p.Range.Text.strip()
        if txt.startswith("TRABAJO PR"):
            r = doc.Range(p.Range.Start, p.Range.End - 1)
            r.Text = TITULO_PORTADA
            r.Font.Size = 35  # tamaño de la plantilla; el TP2 lo achicaba para que entrara el número
            sub = doc.Paragraphs(k + 1)
            r2 = doc.Range(sub.Range.Start, sub.Range.End - 1)
            r2.Text = SUBTITULO_PORTADA
            hechos += 1
            break
    if not hechos:
        raise RuntimeError("No se encontro el titulo de la portada en la copia del TP2")
    # El TP2 trae los datos en cuatro renglones "Etiqueta: dato"; se reemplazan por
    # el bloque de la plantilla, con el mismo aire entre todos los renglones.
    desde = hasta = None
    for k in range(1, 25):
        txt = doc.Paragraphs(k).Range.Text.strip()
        if desde is None and txt.startswith("Alumnos"):
            desde = k
        if desde is not None and txt.startswith("Ciclo Lectivo"):
            hasta = k
            break
    if desde is None or hasta is None:
        raise RuntimeError("No se encontro el bloque de datos de la portada en la copia del TP2")
    bloque = doc.Range(doc.Paragraphs(desde).Range.Start, doc.Paragraphs(hasta).Range.End - 1)
    bloque.Text = "\r".join(t for t, _ in DATOS_PORTADA)
    for i, (_, etiqueta) in enumerate(DATOS_PORTADA):
        p = doc.Paragraphs(desde + i)
        p.Format.SpaceBefore = 0
        p.Format.SpaceAfter = 10
        p.Format.LineSpacingRule = 5  # wdLineSpaceMultiple
        p.Format.LineSpacing = 14.4   # 1,2 renglones, igual que la plantilla
        f = doc.Range(p.Range.Start, p.Range.End - 1).Font
        f.Name = "Arial"
        f.Size = 12
        f.Bold = etiqueta
        f.Underline = 1 if etiqueta else 0
    try:
        doc.BuiltInDocumentProperties("Title").Value = TITULO_DOC
        doc.BuiltInDocumentProperties("Subject").Value = SUBTITULO_PORTADA
    except Exception:
        pass


def equilibrar_indice(doc):
    """Ajusta el aire entre entradas del indice para que todo el indice entre en la pagina 2."""
    toc = doc.TablesOfContents(1)
    for p in toc.Range.Paragraphs:
        if p.Range.Text.replace("\r", "").strip():
            p.Format.SpaceAfter = 1.5


def vaciar_cuerpo(doc):
    """Borra el cuerpo del TP2 desde su primer Titulo 1 posterior al indice.
    Devuelve la plantilla de vinetas del TP2 (numId 5) para reutilizarla."""
    toc_fin = doc.TablesOfContents(1).Range.End
    inicio = None
    plantilla = None
    for p in doc.Range(toc_fin, doc.Content.End).Paragraphs:
        estilo = p.Style.NameLocal
        if inicio is None and estilo in ("Título 1", "Heading 1") and p.Range.Information(12) is False:
            inicio = p.Range.Start
        if plantilla is None and p.Range.ListFormat.ListType == 4:  # wdListBullet
            plantilla = p.Range.ListFormat.ListTemplate
        if inicio is not None and plantilla is not None:
            break
    if inicio is None:
        raise RuntimeError("No se encontro el comienzo del cuerpo del TP2")
    doc.Range(inicio, doc.Content.End).Delete()
    # el ultimo parrafo queda vacio y conserva el salto de seccion
    # (Word funde el parrafo final con el del salto de pagina: hay que reponerlo)
    # El salto de pagina manual del TP2 se reemplaza por "salto de pagina anterior" en
    # el primer titulo: con un indice largo, el salto manual caia en la pagina
    # siguiente y dejaba una pagina en blanco.
    last = doc.Paragraphs.Last
    if "\x0c" in last.Range.Text:
        s = last.Range.Start + last.Range.Text.index("\x0c")
        doc.Range(s, s + 1).Delete()
        last = doc.Paragraphs.Last
    if last.Range.Text != "\r":
        doc.Content.InsertParagraphAfter()
    # el parrafo que cierra el campo de indice queda minimo para no desbordar la pagina
    prev = doc.Paragraphs.Last.Previous()
    if prev is not None and not prev.Range.Text.replace("\r", "").strip():
        prev.Format.SpaceBefore = 0
        prev.Format.SpaceAfter = 0
        prev.Format.LineSpacingRule = wdLineSpaceSingle
        prev.Range.Font.Size = 1
    return plantilla


def num_vinetas_tp2():
    """numId que usan las vinetas del TP2 (numId 5 en la plantilla)."""
    with zipfile.ZipFile(TP2_DOCX) as z:
        x = z.read("word/document.xml").decode("utf-8")
    m = re.search(r'<w:numId w:val="(\d+)"/>', x)
    return m.group(1) if m else None


def normalizar_vinetas(docx):
    """Deja las vinetas exactamente como en el TP2: estilo Normal (sin "Parrafo de
    lista") y la misma lista (numId) que la plantilla. Word, al aplicar la lista por
    COM, crea una lista nueva y cambia el estilo; se corrige en el XML guardado."""
    num = num_vinetas_tp2()
    if not num:
        return 0
    with zipfile.ZipFile(docx) as z:
        entradas = [(i, z.read(i.filename)) for i in z.infolist()]
    cambios = [0]

    def arreglar(m):
        p = m.group(0)
        if "<w:numPr>" not in p:
            return p
        cambios[0] += 1
        p = re.sub(r'<w:pStyle w:val="Prrafodelista"/>', "", p)
        p = re.sub(r'<w:numId w:val="\d+"/>', '<w:numId w:val="%s"/>' % num, p)
        p = p.replace("<w:contextualSpacing/>", "")
        return p

    tmp = docx + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for info, datos in entradas:
            if info.filename == "word/document.xml":
                x = datos.decode("utf-8")
                x = re.sub(r"<w:p\b(?:(?!<w:p\b).)*?</w:p>", arreglar, x, flags=re.S)
                datos = x.encode("utf-8")
            zo.writestr(info, datos)
    os.replace(tmp, docx)
    return cambios[0]


def verificar(doc):
    """Chequeos de formato sobre el resultado. Devuelve lista de observaciones."""
    obs = []
    toc_fin = doc.TablesOfContents(1).Range.End
    pars = doc.Range(toc_fin, doc.Content.End).Paragraphs
    largos = []
    vacios = 0
    for p in pars:
        r = p.Range
        bruto = r.Text
        if "\x0c" in bruto:          # salto de pagina que sigue al indice (del TP2)
            continue
        txt = bruto.replace("\r", "").replace("\x07", "").strip()
        en_tabla = r.Information(12)
        estilo = p.Style.NameLocal
        if en_tabla:
            continue
        if not txt and r.InlineShapes.Count == 0:
            vacios += 1
            continue
        if estilo.startswith(("Título", "Heading")):
            continue
        f = p.Format
        if f.Alignment not in (wdAlignLeft, wdAlignCenter):
            obs.append("Parrafo no alineado a la izquierda: " + txt[:50])
        if f.SpaceAfter < 3:
            obs.append("Parrafo sin espacio posterior: " + txt[:50])
        palabras = len(txt.split())
        if palabras > 55 and f.Alignment == wdAlignLeft:
            largos.append((palabras, txt[:60]))
    if vacios > 1:  # el que cierra el campo de indice es del TP2
        obs.append("Parrafos vacios fuera de cuadros: %d" % vacios)
    for n, t in largos:
        obs.append("Parrafo de %d palabras (maximo 55): %s..." % (n, t))
    return obs


def compactar(doc, max_cambios=20):
    """Evita paginas medio vacias. Con el documento ya paginado, revisa cada figura y
    cada cuadro que empieza arriba de una pagina habiendo dejado mucho blanco en la
    anterior:
      - una captura o un diagrama se achica (hasta ACHIQUE_MAX) si asi entra en el hueco;
      - un diagrama cuya cadena (parrafo que lo presenta + imagen + epigrafe) quedo
        partida en dos paginas se achica hasta que vuelve a entrar junta;
      - un cuadro de mas de cuatro filas deja de ir entero y sigue en la pagina siguiente
        (sin partir filas y repitiendo la de titulos).
    Cada cambio se comprueba repaginando y se deshace si no mejora."""
    ps = doc.PageSetup
    abajo = ps.PageHeight - ps.BottomMargin
    try:
        doc.ActiveWindow.View.Type = 3     # diseno de impresion: posiciones reales
    except Exception:
        pass
    doc.Repaginate()
    toc_fin = doc.TablesOfContents(1).Range.End
    arriba = CUERPO_ARRIBA
    for p in doc.Range(toc_fin, doc.Content.End).Paragraphs:
        if p.Format.PageBreakBefore:
            arriba = p.Range.Information(6)
            break
    alto_cuerpo = abajo - arriba
    originales = {}
    hechos = []

    def pos(k):
        r = doc.Range(k, k)
        return r.Information(3), r.Information(6)

    def inicio_cadena(k):
        s = k
        while s > toc_fin + 2:
            prev = doc.Range(s - 1, s - 1).Paragraphs(1)
            if prev.Range.Information(12) or not prev.Format.KeepWithNext:
                break
            if not prev.Range.Text.replace("\r", "").strip():
                break
            s = prev.Range.Start
        return s

    def bloques():
        out = []
        vistos = set()
        for sh in doc.InlineShapes:
            t = sh.Title
            if t == "fig-captura":
                tb = sh.Range.Tables(1)
                if tb.Range.Start in vistos:
                    continue
                vistos.add(tb.Range.Start)
                pics = [x for x in tb.Range.InlineShapes]
                fin = max(c.Range.End - 2 for c in tb.Range.Cells)
                out.append(("figura", tb.Range.Start, fin, pics, None))
            elif t == "fig-diagrama":
                p = sh.Range.Paragraphs(1)
                epi = p.Next()
                out.append(("figura", p.Range.Start, epi.Range.End - 2, [sh], None))
        for tb in doc.Tables:
            if tb.Range.InlineShapes.Count:
                continue
            epi = doc.Range(tb.Range.End, tb.Range.End).Paragraphs(1)
            out.append(("cuadro", tb.Range.Start, epi.Range.End - 2, [], tb))
        out.sort(key=lambda b: b[1])
        return out

    def hueco_previo(S, pS):
        pP, yP = pos(S - 1)
        if pP != pS - 1:
            return None
        return abajo - (yP + 14)

    def fondo(k):
        pE, yE = pos(k)
        return pE, yE + 12

    for _ in range(max_cambios):
        cambio = False
        doc.Repaginate()
        for tipo, ini, fin, pics, tb in bloques():
            S = inicio_cadena(ini)
            pS, yS = pos(S)
            pE, bE = fondo(fin)
            if pS <= 2:
                continue
            if DEPURAR:
                print("  [compactar]", tipo, (pics[0].AlternativeText[:25] if pics else tb.Cell(1, 1).Range.Text[:12]),
                      "S", pS, round(yS, 1), "fin", pE, round(bE, 1), "arriba", round(arriba, 1),
                      "hueco", hueco_previo(S, pS))
            if tipo == "figura":
                clave = pics[0].AlternativeText
                h = max(x.Height for x in pics)
                h0 = originales.setdefault(clave, h)
                minimo = h0 * (1 - ACHIQUE_MAX)
                nuevos = []
                if pS != pE:                                  # cadena partida
                    nuevos = [h * (1 - 0.05 * k) for k in range(1, 7) if h * (1 - 0.05 * k) >= minimo]
                elif abs(yS - arriba) < 3:
                    gap = hueco_previo(S, pS)
                    if gap is not None and gap > 0.25 * alto_cuerpo:
                        # + 12: el espacio posterior del parrafo previo, que Word respeta
                        need = (bE - arriba) - gap + 16
                        nuevos = [h - need - e for e in range(0, 60, 10) if 0 < need and h - need - e >= minimo]
                for hn in nuevos:
                    for x in pics:
                        x.Height = hn
                    doc.Repaginate()
                    S2 = inicio_cadena(ini)
                    p2, _ = pos(S2)
                    pE2, _ = pos(fin)
                    ok = (p2 == pE2) and (p2 < pS or pS != pE)
                    if ok:
                        hechos.append("%s achicada a %.0f pt (antes %.0f)" % (clave, hn, h))
                        cambio = True
                        break
                    for x in pics:
                        x.Height = h
                    doc.Repaginate()
                if cambio:
                    break
            else:
                n = tb.Rows.Count
                if n < 6 or abs(yS - arriba) >= 3:     # al menos tres filas de cada lado
                    continue
                gap = hueco_previo(S, pS)
                if gap is None or gap < 0.3 * alto_cuerpo:
                    continue
                if not all(tb.Rows(i).Range.ParagraphFormat.KeepWithNext for i in range(3, n - 2)):
                    continue
                for i in range(3, n - 2):
                    tb.Rows(i).Range.ParagraphFormat.KeepWithNext = False
                doc.Repaginate()
                p2, _ = pos(inicio_cadena(tb.Range.Start))
                if p2 < pS:
                    hechos.append("cuadro '%s' sigue en la pagina siguiente" % tb.Cell(1, 1).Range.Text[:-2])
                    cambio = True
                    break
                for i in range(3, n - 2):
                    tb.Rows(i).Range.ParagraphFormat.KeepWithNext = True
                doc.Repaginate()
        if not cambio:
            break
    return hechos


def expandir(doc, ancho_util, alto_max=CAPTURA_ALTO_EXPANDIDA):
    """Llena el blanco al pie de una pagina agrandando la captura que esta en ella. Para cada
    figura de capturas mide el espacio libre al final de su pagina y prueba alturas mayores
    (sin pasar el ancho de su columna ni alto_max). Se queda con la mayor que no mueve nada
    a la pagina siguiente: la primera linea de la pagina siguiente tiene que seguir siendo
    la misma y la cantidad de paginas no puede crecer."""
    ps = doc.PageSetup
    abajo = ps.PageHeight - ps.BottomMargin
    hechos = []

    def pagina_y(k):
        r = doc.Range(k, k)
        return r.Information(3), r.Information(6)

    def inicio_pagina(n):
        try:
            return doc.GoTo(1, 1, n).Start      # wdGoToPage, wdGoToAbsolute
        except Exception:
            return None

    doc.Repaginate()
    tablas = []
    vistos = set()
    for sh in doc.InlineShapes:
        if sh.Title != "fig-captura":
            continue
        tb = sh.Range.Tables(1)
        if tb.Range.Start in vistos:
            continue
        vistos.add(tb.Range.Start)
        tablas.append(tb.Range.Start)

    for inicio in tablas:
        doc.Repaginate()
        tb = doc.Range(inicio, inicio + 1).Tables(1)
        pics = [x for x in tb.Range.InlineShapes]
        ncols = tb.Columns.Count
        pag, _ = pagina_y(tb.Range.Start)
        pag_fin, _ = pagina_y(tb.Range.End - 1)
        if pag != pag_fin:
            continue
        paginas = doc.ComputeStatistics(2)
        sig = inicio_pagina(pag + 1) if pag < paginas else None
        if sig is None or sig <= tb.Range.End:
            continue
        # espacio libre: entre la ultima linea de la pagina y el margen inferior
        _, y_ult = pagina_y(sig - 1)
        libre = abajo - (y_ult + 14)
        if libre < 20:
            continue
        h = max(x.Height for x in pics)
        apaisada = ncols == 1 and pics[0].Width > pics[0].Height   # igual que en capturas(): un par nunca ocupa el ancho entero
        celda = (ancho_util if apaisada or ncols == 1 else ancho_util / ncols) - 2 * TABLA_PAD_H - 4
        tope = min(alto_max, min(celda * x.Height / x.Width for x in pics))
        if DEPURAR:
            print("  [expandir]", pics[0].AlternativeText[:30], "pag", pag, "libre", round(libre), "h", round(h), "tope", round(tope))
        if tope <= h + 4:
            continue
        primera = doc.Range(sig, sig + 20).Text
        mejor = h
        for nuevo in sorted({min(tope, h + libre - d) for d in (4, 14, 28, 44, 64, 90)}, reverse=True):
            if nuevo <= mejor + 4:
                continue
            for x in pics:
                x.Height = nuevo
            doc.Repaginate()
            sig2 = inicio_pagina(pag + 1)
            ok = (doc.ComputeStatistics(2) == paginas and sig2 is not None
                  and doc.Range(sig2, sig2 + 20).Text == primera)
            if ok:
                mejor = nuevo
                break
        for x in pics:
            x.Height = mejor
        doc.Repaginate()
        if mejor > h + 4:
            hechos.append("%s agrandada a %.0f pt (antes %.0f)" % (pics[0].AlternativeText, mejor, h))
    return hechos


def huecos_pdf(pdf, desde=3, umbral=0.4):
    """Paginas (salvo la ultima) cuyo contenido termina antes del 60 % del cuerpo."""
    d = fitz.open(pdf)
    out = []
    for i in range(desde - 1, d.page_count - 1):
        pg = d[i]
        arriba, abajo = CUERPO_ARRIBA - 5, pg.rect.height - 72
        ys = [b[3] for b in pg.get_text("blocks") if b[1] >= arriba and b[3] <= abajo]
        ys += [r.y1 for img in pg.get_images(full=True) for r in pg.get_image_rects(img[0])
               if r.y0 >= arriba - 5 and r.y1 <= abajo + 5]
        for dr in pg.get_drawings():
            r = dr["rect"]
            if r.y0 >= arriba and r.y1 <= abajo:
                ys.append(r.y1)
        fin = max(ys) if ys else arriba
        libre = (abajo - fin) / (abajo - arriba)
        if libre > umbral:
            out.append((i + 1, round(libre * 100)))
    d.close()
    return out


def renderizar(pdf, carpeta, zoom=1.3):
    os.makedirs(carpeta, exist_ok=True)
    for f in os.listdir(carpeta):
        if f.startswith("pag-") and f.endswith(".png"):
            os.remove(os.path.join(carpeta, f))
    d = fitz.open(pdf)
    for i, pg in enumerate(d, 1):
        pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(os.path.join(carpeta, "pag-%02d.png" % i))
    n = d.page_count
    d.close()
    return n


def main():
    ap = argparse.ArgumentParser(description="Genera el informe del TP3 a partir de contenido.md")
    ap.add_argument("--contenido", default=CONTENIDO)
    ap.add_argument("--salida", default=SALIDA_DOCX, help="ruta del .docx; el PDF se guarda al lado")
    ap.add_argument("--capturas", action="append", help="carpeta de capturas (repetible)")
    ap.add_argument("--diagramas", action="append", help="carpeta de diagramas SVG/PNG (repetible)")
    ap.add_argument("--render", default=None, help="carpeta para las paginas renderizadas")
    ap.add_argument("--sin-render", action="store_true")
    a = ap.parse_args()

    salida = os.path.abspath(a.salida)
    pdf = os.path.splitext(salida)[0] + ".pdf"
    render = a.render or os.path.join(AQUI, "render")
    capturas_dirs = [os.path.abspath(d) for d in (a.capturas or [])] + CAPTURAS_DIRS
    diagramas_dirs = [os.path.abspath(d) for d in (a.diagramas or [])] + DIAGRAMAS_DIRS

    with open(a.contenido, encoding="utf-8") as fh:
        bloques = parse_md(fh.read())
    print("Bloques leidos:", len(bloques))

    if not os.path.isfile(TP2_DOCX):
        sys.exit("No existe la plantilla del TP2: " + TP2_DOCX)
    for ruta in (salida, pdf):
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except PermissionError:
                sys.exit("El archivo esta abierto en otro programa, cerralo y reintenta: " + ruta)
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    shutil.copy2(TP2_DOCX, salida)   # el TP2 nunca se abre ni se modifica

    tmpdir = tempfile.mkdtemp(prefix="tp3_informe_", dir=AQUI)
    pythoncom.CoInitialize()
    word = None
    doc = None
    t0 = time.time()
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.ScreenUpdating = False
        doc =word.Documents.Open(salida, False, False, False)
        doc.TrackRevisions = False

        preparar_portada(doc)
        plantilla = vaciar_cuerpo(doc)
        g = Generador(doc, capturas_dirs, diagramas_dirs, tmpdir)

        previo = None
        for k, b in enumerate(bloques):
            tipo = b[0]
            sig = bloques[k + 1][0] if k + 1 < len(bloques) else None
            if tipo == "h1":
                g.titulo(b[1], 1)
            elif tipo == "h2":
                g.titulo(b[1], 2)
            elif tipo == "p":
                p = g.parrafo(b[1])
                # el parrafo que presenta una lista, un cuadro o una figura queda con ella
                # las capturas no: si no entran, pasan solas a la pagina siguiente y el texto
                # queda al pie de la anterior, sin dejar media pagina en blanco
                if sig in ("lista", "tabla", "diagrama"):
                    p.Format.KeepWithNext = True
                    p.Format.KeepTogether = True
            elif tipo == "lista":
                g.lista(b[1], plantilla)
            elif tipo == "tabla":
                g.tabla(b[1], b[2], b[3])
            elif tipo == "capturas":
                g.capturas(b[1])
            elif tipo == "diagrama":
                g.diagrama(b[1], b[2])
            previo = tipo

        doc.Save()
        doc.Close(False)
        doc = None

        # vinetas con el estilo y la lista del TP2 (correccion sobre el XML)
        nv = normalizar_vinetas(salida)

        # segunda apertura: indice actualizado, verificacion y PDF
        doc = word.Documents.Open(salida, False, False, False)
        word.ScreenUpdating = True
        doc.Repaginate()
        ajustes = compactar(doc)
        ajustes += expandir(doc, doc.PageSetup.PageWidth - doc.PageSetup.LeftMargin - doc.PageSetup.RightMargin)
        toc = doc.TablesOfContents(1)
        toc.Update()
        equilibrar_indice(doc)
        doc.Repaginate()
        toc.Update()
        equilibrar_indice(doc)
        doc.Repaginate()

        obs = verificar(doc)
        for p in doc.Paragraphs:
            if p.Range.ListFormat.ListType != 0 and p.Style.NameLocal != "Normal":
                obs.append("Vineta con estilo distinto de Normal: " + p.Range.Text[:50])
        paginas = doc.ComputeStatistics(2)
        palabras = doc.ComputeStatistics(0)
        doc.Save()
        doc.ExportAsFixedFormat(pdf, wdExportFormatPDF, False, 0, 0, 1, 1, 0, True, True, 1)
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("DOCX:", salida)
    print("PDF: ", pdf)
    print("Paginas: %d | palabras (todo el documento): %d | %.1f s" % (paginas, palabras, time.time() - t0))
    print("Marcadores de dato pendientes: %d | vinetas normalizadas: %d" % (g.datos, nv))
    if g.pendientes:
        print("Capturas o diagramas pendientes (%d): %s" % (len(g.pendientes), ", ".join(g.pendientes)))
    for a_ in ajustes:
        print("AJUSTE:", a_)
    for o in obs:
        print("OBS:", o)
    for n_, libre in huecos_pdf(pdf):
        print("OBS: pagina %d con %d %% del cuerpo libre" % (n_, libre))
    if not a.sin_render:
        n = renderizar(pdf, render)
        print("Paginas renderizadas: %d en %s" % (n, render))


if __name__ == "__main__":
    main()
