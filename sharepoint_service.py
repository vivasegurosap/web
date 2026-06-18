from sharepoint import obtener_token
import requests
from datetime import datetime

SITE_ID = os.getenv("SITE_ID")
LIST_ID = os.getenv("LIST_ID")

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

    return respuesta.status_code, respuesta.text