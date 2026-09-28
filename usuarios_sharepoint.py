import requests

from sharepoint import obtener_token

SITE_ID = "ltdavivaseguros.sharepoint.com,d19e975d-3de3-41ae-8e04-f8b3cb41d412,9de98400-fdc6-40d6-ba92-cb96c8091105"

USUARIOS_LIST_ID = "7be25a36-209b-4b09-bc04-c95bbf91a954"


def buscar_usuario(username):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{USUARIOS_LIST_ID}/items?expand=fields"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(r.text)

    items = r.json()["value"]

    for item in items:

        fields = item["fields"]

        if fields.get("Username", "").lower() == username.lower():

            return {
                "id": item["id"],
                "username": fields.get("Username"),
                "password_hash": fields.get("PasswordHash"),
                "nombre_completo": fields.get("NombreCompleto"),
                "rol": fields.get("Rol"),
                "activo": fields.get("Activo"),
                "correo": fields.get("Correo"),
                "password_temporal": fields.get("PasswordTemporal", False)
            }

    return None
def buscar_usuario_por_correo(correo):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{USUARIOS_LIST_ID}/items?expand=fields"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(r.text)

    items = r.json()["value"]

    for item in items:

        fields = item["fields"]

        if fields.get("Correo", "").lower() == correo.lower():

            return {
                "id": item["id"],
                "username": fields.get("Username"),
                "password_hash": fields.get("PasswordHash"),
                "nombre_completo": fields.get("NombreCompleto"),
                "rol": fields.get("Rol"),
                "activo": fields.get("Activo"),
                "correo": fields.get("Correo"),
                "password_temporal": fields.get("PasswordTemporal", False)
            }

    return None
def buscar_usuario_por_id(user_id):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{USUARIOS_LIST_ID}/items?expand=fields"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(r.text)

    items = r.json()["value"]

    for item in items:

        if str(item["id"]) == str(user_id):

            fields = item["fields"]

            return {
                "id": item["id"],
                "username": fields.get("Username"),
                "password_hash": fields.get("PasswordHash"),
                "nombre_completo": fields.get("NombreCompleto"),
                "rol": fields.get("Rol"),
                "activo": fields.get("Activo"),
                "correo": fields.get("Correo"),
                "password_temporal": fields.get("PasswordTemporal", False)
            }

    return None

def actualizar_password_usuario(user_id, password_hash, temporal=False):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{USUARIOS_LIST_ID}/items/{user_id}/fields"
    )

    datos = {
        "PasswordHash": password_hash,
        "PasswordTemporal": temporal
    }

    r = requests.patch(
        url,
        headers=headers,
        json=datos
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return True
def actualizar_password_definitiva(user_id, password_hash):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}"
        f"/lists/{USUARIOS_LIST_ID}/items/{user_id}/fields"
    )

    datos = {

        "PasswordHash": password_hash,

        "PasswordTemporal": False

    }

    r = requests.patch(
        url,
        headers=headers,
        json=datos
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return True
def obtener_todos_los_usuarios():

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{USUARIOS_LIST_ID}/items?expand=fields"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(r.text)

    usuarios = {}

    for item in r.json()["value"]:

        fields = item["fields"]

        usuarios[str(item["id"])] = {
            "id": item["id"],
            "nombre_completo": fields.get("NombreCompleto"),
            "correo": fields.get("Correo"),
            "rol": fields.get("Rol")
        }

    return usuarios