import requests
from msal import ConfidentialClientApplication

import os

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPES = ["https://graph.microsoft.com/.default"]


def obtener_token():

    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    resultado = app.acquire_token_for_client(
        scopes=SCOPES
    )

    if "access_token" not in resultado:
        raise Exception(resultado)

    return resultado["access_token"]


def probar_conexion():

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    respuesta = requests.get(
        "https://graph.microsoft.com/v1.0/sites",
        headers=headers
    )

    print("STATUS:", respuesta.status_code)
    print(respuesta.text)