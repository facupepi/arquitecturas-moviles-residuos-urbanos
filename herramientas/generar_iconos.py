"""Genera app/vendor/lucide.min.js con solo los íconos que usa la app (de 358 KB a unos 25 KB).

Detecta los nombres de ícono presentes en app/index.html y empaqueta esos con esbuild.
Uso (desde herramientas/, con `npm install` hecho): python generar_iconos.py
"""
import pathlib, re, subprocess, sys

AQUI = pathlib.Path(__file__).resolve().parent
html = (AQUI.parent / "app/index.html").read_text(encoding="utf-8")
# nombre en PascalCase (incluye alias antiguos) -> archivo del ícono
alias = {}
for linea in (AQUI / "node_modules/lucide/dist/esm/iconsAndAliases.js").read_text(encoding="utf-8").splitlines():
    m = re.match(r"export \{(.*)\} from '\./icons/([a-z0-9-]+)\.js'", linea)
    if m:
        for nombre in re.findall(r"default as ([A-Za-z0-9]+)", m.group(1)):
            alias[nombre] = m.group(2)
pascal = lambda k: "".join(p.capitalize() for p in k.split("-"))
usados = sorted(t for t in set(re.findall(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", html)) if pascal(t) in alias)

entrada = ["import { createIcons as crear } from 'lucide/dist/esm/lucide.js';"]
entrada += [f"import {pascal(n)} from 'lucide/dist/esm/icons/{alias[pascal(n)]}.js';" for n in usados]
entrada.append("const icons = { " + ", ".join(pascal(n) for n in usados) + " };")
entrada.append("window.lucide = { createIcons: (o) => crear(Object.assign({ icons }, o)) };")
(AQUI / "iconos_entrada.js").write_text("\n".join(entrada) + "\n", encoding="utf-8")

salida = AQUI.parent / "app/vendor/lucide.min.js"
subprocess.run(["npx", "esbuild", "iconos_entrada.js", "--bundle", "--minify", "--format=iife",
                f"--outfile={salida}", "--banner:js=/* lucide 0.469.0 (ISC), solo los íconos usados */"], cwd=AQUI, check=True, shell=True)
print(len(usados), "íconos;", salida.stat().st_size, "bytes")
