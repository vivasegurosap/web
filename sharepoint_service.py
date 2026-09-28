import requests
from sharepoint import obtener_token
from datetime import datetime
import os
from usuarios_sharepoint import obtener_todos_los_usuarios
import mimetypes


SITE_ID = os.getenv("SITE_ID")
LIST_ID = os.getenv("LIST_ID")
DOCUMENTOS_DRIVE_ID = os.getenv("DOCUMENTOS_DRIVE_ID")
print("DRIVE ID:", DOCUMENTOS_DRIVE_ID)

def crear_solicitud_sharepoint(
    radicado,
    razon_social,
    nombre_remitente,
    correo_contacto,
    telefono_contacto,
    poliza,
    tipo_solicitud,
    descripcion,
    asignado_a,
    creado_por
):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer " + token,
        "Content-Type": "application/json"
    }

    datos = {
        "fields": {
            "Title": radicado,
            "Radicado": radicado,
            "FechaCreacion": datetime.now().isoformat(),
            "RazonSocial": razon_social,
            "NombreRemitente": nombre_remitente,
            "CorreoContacto": correo_contacto,
            "TelefonoContacto": telefono_contacto,
            "Poliza": poliza,
            "TipoSolicitud": tipo_solicitud,
            "Descripcion": descripcion,
            "Estado": "Recibido",
            "AsignadoA": str(asignado_a),
            "CreadoPor": str(creado_por)
        }
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items"

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos
    )

    print("STATUS SHAREPOINT:", respuesta.status_code)
    print("RESPUESTA SHAREPOINT:", respuesta.text)

    if respuesta.status_code not in [200, 201]:
        raise Exception(respuesta.text)

    item_id = respuesta.json()["id"]

    return respuesta.status_code, item_id
def obtener_solicitudes():
    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items?$expand=fields&$orderby=createdDateTime desc"

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise Exception(resp.text)

    items = resp.json()["value"]
    usuarios = obtener_todos_los_usuarios()
    solicitudes = []

    for item in items:

        f = item["fields"]

        nombre_asignado = ""

        usuario = usuarios.get(str(f.get("AsignadoA")))

        if usuario:
            nombre_asignado = usuario["nombre_completo"]

        solicitudes.append({
            "id": item["id"],
            "radicado": f.get("Radicado"),
            "razon_social": f.get("RazonSocial"),
            "nombre_remitente": f.get("NombreRemitente"),
            "tipo_solicitud": f.get("TipoSolicitud"),
            "estado": f.get("Estado"),
            "asignado_a": f.get("AsignadoA"),
            "asignado_nombre": nombre_asignado,
            "creado_por": f.get("CreadoPor"),
            "fecha_creacion": datetime.fromisoformat(
                f.get("FechaCreacion").replace("Z", "+00:00")
            ) if f.get("FechaCreacion") else None,
            "fecha_cierre": datetime.fromisoformat(
                f.get("FechaCierre").replace("Z", "+00:00")
            ) if f.get("FechaCierre") else None,
        })
    solicitudes.sort(key=lambda x: x["fecha_creacion"].timestamp() if x["fecha_creacion"] else 0, reverse=True)
    return solicitudes

def contar_solicitudes():
    data = obtener_solicitudes()

    total = len(data)
    pendientes = len([s for s in data if s.get("estado") == "Pendiente"])
    proceso = len([s for s in data if s.get("estado") == "En proceso"])
    resueltos = len([s for s in data if s.get("estado") == "Resuelto"])
    cerrados = len([s for s in data if s.get("estado") == "Cerrado"])

    return total, pendientes, proceso, resueltos, cerrados

CONFIG_LIST_ID = os.getenv("CONFIG_LIST_ID")

def obtener_siguiente_radicado():

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{CONFIG_LIST_ID}/items?$expand=fields"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(f"Error consultando consecutivo: {r.text}")

    datos = r.json().get("value", [])

    if not datos:
        raise Exception(
            "La lista ConfiguracionCRM está vacía. Debe existir un registro inicial."
        )

    item = datos[0]

    item_id = item["id"]
    consecutivo = int(item["fields"]["Valor"])

    nuevo_consecutivo = consecutivo + 1

    url_update = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{CONFIG_LIST_ID}/items/{item_id}/fields"

    body = {
        "Valor": nuevo_consecutivo
    }

    r2 = requests.patch(
        url_update,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        json=body
    )

    if r2.status_code not in [200, 204]:
        raise Exception(f"Error actualizando consecutivo: {r2.text}")

    radicado = f"RAD-{nuevo_consecutivo:06d}"

    return radicado

USUARIOS_LIST_ID = os.getenv("USUARIOS_LIST_ID")

def obtener_usuarios_internos():

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{USUARIOS_LIST_ID}/items?$expand=fields"
    )

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(f"Error obteniendo usuarios: {r.text}")

    datos = r.json().get("value", [])

    usuarios = []

    for item in datos:

        campos = item["fields"]

        print("CAMPOS:", campos)

        if (
            campos.get("Rol") == "interno"
            and campos.get("Activo") is True
        ):

            usuarios.append({
                "id": item["id"],
                "nombre_completo": campos.get("NombreCompleto")
            })

    print("USUARIOS INTERNOS:", usuarios)

    return usuarios

def obtener_usuario_por_id(id_usuario):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{USUARIOS_LIST_ID}/items/{id_usuario}?$expand=fields"
    )

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return None

    campos = r.json()["fields"]

    return {
        "id": id_usuario,
        "nombre_completo": campos.get("NombreCompleto"),
        "username": campos.get("Username"),
        "rol": campos.get("Rol")
    }

def actualizar_estado_solicitud(item_id, nuevo_estado, atendido_por):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    datos = {
        "Estado": nuevo_estado,
        "AtendidoPor": atendido_por
    }

    if nuevo_estado in ["Resuelto", "Cerrado"]:
        datos["FechaCierre"] = datetime.now().isoformat()

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{LIST_ID}/items/{item_id}/fields"
    )

    respuesta = requests.patch(
        url,
        headers=headers,
        json=datos
    )

    print("DATOS ENVIADOS:", datos)
    print("STATUS ACTUALIZAR:", respuesta.status_code)
    print("RESPUESTA ACTUALIZAR:", respuesta.text)

    if respuesta.status_code not in [200, 204]:
        raise Exception(
            f"Error actualizando estado: {respuesta.text}"
        )

    return True

def obtener_solicitud_por_id(item_id):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{LIST_ID}/items/{item_id}?$expand=fields"
    )

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(r.text)

    item = r.json()

    f = item["fields"]
    usuario = obtener_usuario_por_id(
    f.get("AsignadoA")
    )

    nombre_asignado = ""

    if usuario:
        nombre_asignado = usuario.get(
            "nombre_completo"
        )
    return {
        "id": item["id"],
        "radicado": f.get("Radicado"),
        "razon_social": f.get("RazonSocial"),
        "nombre_remitente": f.get("NombreRemitente"),
        "correo_contacto": f.get("CorreoContacto"),
        "telefono_contacto": f.get("TelefonoContacto"),
        "poliza": f.get("Poliza"),
        "tipo_solicitud": f.get("TipoSolicitud"),
        "descripcion": f.get("Descripcion"),
        "estado": f.get("Estado"),
        "asignado_a": f.get("AsignadoA"),
        "asignado_nombre": nombre_asignado,
        "creado_por": f.get("CreadoPor"),
        "fecha_creacion": f.get("FechaCreacion"),
        "fecha_cierre": f.get("FechaCierre"),
        "atendido_por": f.get("AtendidoPor")
    }

def obtener_adjuntos_solicitud(radicado):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("RADICADO:", radicado)

    url = (
        f"https://graph.microsoft.com/v1.0/drives/"
        f"{DOCUMENTOS_DRIVE_ID}/root:/{radicado}:/children"
    )

    r = requests.get(url, headers=headers)

    print("URL:", url)
    print("STATUS:", r.status_code)
    print("RESPUESTA ADJUNTOS:", r.text)

    if r.status_code != 200:
        print("No existen adjuntos")
        return []

    datos = r.json()
    from datetime import datetime

    adjuntos = []

    for archivo in datos.get("value", []):

        fecha = None

        if archivo.get("createdDateTime"):
            fecha = datetime.fromisoformat(
                archivo["createdDateTime"].replace("Z", "+00:00")
            )

        adjuntos.append({

            "nombre_archivo": archivo["name"],
            "url": archivo["@microsoft.graph.downloadUrl"],
            "fecha": fecha

        })

    return adjuntos

def obtener_adjuntos_para_correo(radicado):

    adjuntos = obtener_adjuntos_solicitud(radicado)

    archivos = []

    for archivo in adjuntos:

        r = requests.get(archivo["url"])

        if r.status_code == 200:

            mime = mimetypes.guess_type(archivo["nombre_archivo"])[0]

            if mime is None:
                mime = "application/octet-stream"

            archivos.append({
                "nombre": archivo["nombre_archivo"],
                "mime": mime,
                "contenido": r.content
            })

    return archivos

def subir_adjunto(radicado, archivo):

    token = obtener_token()

    nombre_archivo = archivo.filename

    url = (
        f"https://graph.microsoft.com/v1.0/drives/"
        f"{DOCUMENTOS_DRIVE_ID}/root:/{radicado}/{nombre_archivo}:/content"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }

    response = requests.put(
        url,
        headers=headers,
        data=archivo.read()
    )

    print("STATUS ADJUNTO:", response.status_code)
    print("RESPUESTA ADJUNTO:", response.text)

    return response.status_code

def crear_carpeta_radicado(radicado):

    token = obtener_token()

    url = (
        f"https://graph.microsoft.com/v1.0/drives/"
        f"{DOCUMENTOS_DRIVE_ID}/root/children"
    )

    body = {
        "name": radicado,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "replace"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json=body
    )

    print("STATUS CARPETA:", response.status_code)
    print("RESPUESTA CARPETA:", response.text)

def obtener_adjuntos_radicado(radicado):

    token = obtener_token()

    url = (
        f"https://graph.microsoft.com/v1.0/drives/"
        f"{DOCUMENTOS_DRIVE_ID}/root:/{radicado}:/children"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    print("STATUS LISTA ARCHIVOS:", response.status_code)
    print("RESPUESTA ARCHIVOS:", response.text)

    if response.status_code != 200:
        return []

    datos = response.json()

    archivos = []

    for archivo in datos.get("value", []):

        archivos.append({
            "nombre_archivo": archivo["name"],
            "url_descarga": archivo.get(
                "@microsoft.graph.downloadUrl"
            )
        })

    return archivos

def crear_item_sharepoint(lista_id, datos):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{lista_id}/items"
    )

    payload = {
        "fields": datos
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print("STATUS CREAR ITEM:", respuesta.status_code)
    print("RESPUESTA:", respuesta.text)

    if respuesta.status_code not in [200, 201]:
        raise Exception(respuesta.text)

    return respuesta.json()

def eliminar_item_sharepoint(lista_id, item_id):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{lista_id}/items/{item_id}"
    )

    respuesta = requests.delete(url, headers=headers)

    print("STATUS ELIMINAR:", respuesta.status_code)

    if respuesta.status_code != 204:
        raise Exception(respuesta.text)

    return True

def actualizar_item_sharepoint(lista_id, item_id, datos):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{lista_id}/items/{item_id}/fields"
    )

    respuesta = requests.patch(
        url,
        headers=headers,
        json=datos
    )

    print("STATUS UPDATE:", respuesta.status_code)
    print("RESPUESTA UPDATE:", respuesta.text)

    if respuesta.status_code not in [200, 204]:
        raise Exception(respuesta.text)

    return True