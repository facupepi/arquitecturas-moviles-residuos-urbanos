"""Asigna el rol de una cuenta de Google (colección roles_por_correo, que solo escribe la administración).

  python asignar_rol.py correo@gmail.com autoridad     # o recolector
  python asignar_rol.py correo@gmail.com ninguno       # quita el rol (queda como vecino)
Usa la sesión del CLI de Firebase (`firebase login`). Los correos no se guardan en el repositorio.
"""
import json, sys, urllib.parse, urllib.request
import admin_nube

if len(sys.argv) != 3 or sys.argv[2] not in ("autoridad", "recolector", "ninguno"):
    sys.exit(__doc__)
correo, rol = sys.argv[1].strip().lower(), sys.argv[2]
url = f"{admin_nube.BASE}/roles_por_correo/{urllib.parse.quote(correo, safe='')}"
cab = {"Authorization": f"Bearer {admin_nube._token()}", "Content-Type": "application/json"}
if rol == "ninguno":
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="DELETE", headers=cab))
    except urllib.error.HTTPError:
        pass
    print(correo, "-> vecino")
else:
    urllib.request.urlopen(urllib.request.Request(url, json.dumps({"fields": {"rol": {"stringValue": rol}}}).encode(), method="PATCH", headers=cab))
    print(correo, "->", rol)
