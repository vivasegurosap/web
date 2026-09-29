import os
import base64
import requests
from pathlib import Path
from flask import current_app

def crear_html_resolucion(solicitud, respuesta):

    return f"""
<html>
<head>
<meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#edf2f7;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#edf2f7;padding:40px 0;">
<tr>
<td align="center">
<table width="500" cellpadding="0" cellspacing="0"
style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 35px rgba(0,0,0,.10);">
<tr>
<td style="background:#1F7A83;padding:15px 20px;text-align:center;">
<img
    src="cid:logo_viva"
    width="110"
    style="
        width:110px;
        max-width:110px;
        height:auto;
        display:block;
        margin:0 auto 20px auto;
        border:0;
    ">
<h1 style="margin:0;color:white;font-size:24px;font-weight:700;">
Portal de Solicitudes VivaAP
</h1>
<p style="margin-top:6px;font-size:15px;color:white;">
Vivaseguros Agencia de Seguros Ltda.
</p>
</td>
</tr>
<tr>
<td style="padding:40px 45px 15px 45px;">
<div style="
background:linear-gradient(90deg,#e8fff0,#f8fffb);
border:2px solid #7cd992;
border-radius:14px;
padding:28px;
text-align:center;
box-shadow:0 4px 12px rgba(0,0,0,.05);
">
<div style="
font-size:48px;
margin-bottom:10px;
">
✅
</div>
<div style="
font-size:24px;
font-weight:700;
color:#177245;
">
Solicitud Gestionada Exitosamente
</div>
<div style="
margin-top:12px;
font-size:15px;
color:#4f6360;
">
La atención correspondiente a este radicado ha finalizado satisfactoriamente.
</div>
</div>
</td>
</tr>
<tr>
<td style="padding:15px 45px 10px 45px;">
<p style="font-size:22px;color:#2d3748;margin:0;">
Estimado(a)
<strong>{solicitud["nombre_remitente"]}</strong>,
</p>
<p style="margin-top:28px;font-size:16px;line-height:1.9;color:#4a5568;">
Reciba un cordial saludo.
</p>
<p style="font-size:16px;line-height:1.9;color:#4a5568;">
Agradecemos la confianza depositada en
<strong>Vivaseguros Agencia de Seguros Ltda.</strong>
</p>
<p style="font-size:16px;line-height:1.9;color:#4a5568;">
Nos complace informarle que la gestión correspondiente a su solicitud ha sido atendida satisfactoriamente por nuestro equipo.
A continuación encontrará el resumen de la gestión realizada.
</p>
</td>
</tr>
<tr>
<td style="padding:0 45px;">
<div style="margin:35px 0;border:1px solid #dfe6ee;border-radius:12px;overflow:hidden;">
<div style="background:#1F7A83;color:white;padding:16px 22px;font-size:18px;font-weight:bold;">
Resumen de la Solicitud
</div>
<table width="100%" cellpadding="14" cellspacing="0" style="border-collapse:collapse;">
<tr style="background:#fafbfd;">
<td width="35%" style="font-weight:bold;color:#34495e;">Radicado</td>
<td style="font-weight:bold;color:#1F7A83;font-size:17px;">
{solicitud["radicado"]}
</td>
</tr>
<tr>
<td style="font-weight:bold;color:#34495e;">Empresa</td>
<td>{solicitud["razon_social"]}</td>
</tr>
<tr style="background:#fafbfd;">
<td style="font-weight:bold;color:#34495e;">Tipo de Solicitud</td>
<td>{solicitud["tipo_solicitud"]}</td>
</tr>
<tr>
<td style="font-weight:bold;color:#34495e;">Estado</td>
<td>
<span style="
background:#d4edda;
color:#155724;
padding:7px 16px;
border-radius:20px;
font-weight:bold;
font-size:14px;
display:inline-block;
">
✔ RESUELTO
</span>
</td>
</tr>
</table>
</div>
</td>
</tr>
<tr>
<td style="padding:0 45px;">
<div style="margin-top:40px;">
<div style="
background:#1F7A83;
color:white;
padding:16px 22px;
font-size:18px;
font-weight:bold;
border-radius:12px 12px 0 0;
">
Resultado de la Gestión
</div>
<div style="
border:1px solid #dfe6ee;
border-top:none;
padding:30px;
background:#fcfcfc;
border-radius:0 0 12px 12px;
">
<p style="
margin-top:0;
margin-bottom:18px;
font-size:15px;
font-weight:bold;
color:#1F7A83;
">
Nuestro equipo realizó la siguiente gestión para atender su solicitud:
</p>
<div style="
background:white;
border-left:6px solid #1F7A83;
padding:22px;
border-radius:8px;
font-size:16px;
line-height:1.9;
color:#444;
box-shadow:0 2px 8px rgba(0,0,0,.05);
">
{respuesta if respuesta else "La solicitud fue gestionada satisfactoriamente por nuestro equipo."}
</div>
</div>
</div>
<div style="
margin-top:35px;
padding:22px;
background:#eef8ff;
border-left:5px solid #1F7A83;
border-radius:8px;
">
<p style="
margin:0;
font-size:16px;
line-height:1.8;
color:#34495e;
">
📎 <strong>Documentos adjuntos</strong>
<br><br>
En este correo encontrará los documentos correspondientes a la gestión realizada.
Le recomendamos conservar este mensaje como soporte de la atención brindada.
</p>
</div>
<hr style="
margin-top:45px;
margin-bottom:35px;
border:none;
height:1px;
background:#d9dee5;
">
<p style="
font-size:16px;
line-height:1.9;
color:#4a5568;
">
Esperamos que la información suministrada haya dado respuesta a su solicitud.
</p>
<p style="
font-size:16px;
line-height:1.9;
color:#4a5568;
">
Agradecemos la confianza depositada en nuestra organización y reiteramos nuestro compromiso de brindarle un servicio oportuno, transparente y de calidad.
</p>
<div style="
margin-top:40px;
padding:28px;
background:#f8fafc;
border-radius:12px;
border:1px solid #e2e8f0;
">
<p style="
margin:0;
font-size:18px;
font-weight:bold;
color:#1F7A83;
">
Equipo Operativo
</p>
<p style="
margin-top:10px;
margin-bottom:0;
font-size:15px;
color:#4a5568;
line-height:1.8;
">
Portal de Solicitudes VivaAP
<br>
Vivaseguros Agencia de Seguros Ltda.
</p>
</div>
</div>
</td>
</tr>
<tr>
<td style="
background:#1F7A83;
padding:22px;
text-align:center;
color:white;
">
<p style="
margin:0;
font-size:14px;
">
Este correo fue generado automáticamente por el
<strong>Portal de Solicitudes VivaAP</strong>
</p>
<p style="
margin-top:10px;
font-size:13px;
opacity:.9;
">
Por favor, no responda este mensaje de manera automática.
</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>
"""
def enviar_correo_resolucion(solicitud, html, adjuntos=None):

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    correo_remitente = os.getenv("MAIL_USERNAME")

    if not tenant_id:
        raise Exception("Falta TENANT_ID en las variables de entorno.")

    if not client_id:
        raise Exception("Falta CLIENT_ID en las variables de entorno.")

    if not client_secret:
        raise Exception("Falta CLIENT_SECRET en las variables de entorno.")

    if not correo_remitente:
        raise Exception("Falta MAIL_USERNAME en las variables de entorno.")

    # =========================================================
    # 1. Obtener token de Microsoft Graph
    # =========================================================

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}/oauth2/v2.0/token"
    )

    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token_response = requests.post(
        token_url,
        data=token_data,
        timeout=20
    )

    if token_response.status_code != 200:
        raise Exception(
            f"Error obteniendo token de Microsoft Graph: "
            f"{token_response.status_code} - "
            f"{token_response.text}"
        )

    access_token = token_response.json()["access_token"]

    # =========================================================
    # 2. Preparar destinatario
    # =========================================================

    destinatario = solicitud["correo_contacto"]

    if not destinatario:
        raise Exception("La solicitud no tiene correo de contacto.")

    # =========================================================
    # 3. Logo embebido
    # =========================================================

    logo = (
        Path(current_app.root_path)
        / "static"
        / "VivaSeguros_Logo2025_Blanco.png"
    )

    if not logo.exists():
        raise Exception(
            f"No se encontró el logo: {logo}"
        )

    with open(logo, "rb") as f:
        logo_base64 = base64.b64encode(
            f.read()
        ).decode("utf-8")

    # =========================================================
    # 4. Crear adjuntos para Microsoft Graph
    # =========================================================

    attachments = [
        {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": "VivaSeguros_Logo2025_Blanco.png",
            "contentType": "image/png",
            "contentBytes": logo_base64,
            "isInline": True,
            "contentId": "logo_viva"
        }
    ]

    if adjuntos:

        for archivo in adjuntos:

            contenido = archivo["contenido"]

            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": archivo["nombre"],
                "contentType": archivo["mime"],
                "contentBytes": base64.b64encode(
                    contenido
                ).decode("utf-8")
            })

    # =========================================================
    # 5. Construir mensaje
    # =========================================================

    mensaje = {
        "message": {
            "subject": (
                f"Respuesta a la solicitud "
                f"{solicitud['radicado']}"
            ),

            "body": {
                "contentType": "HTML",
                "content": html
            },

            "toRecipients": [
                {
                    "emailAddress": {
                        "address": destinatario
                    }
                }
            ],

            "attachments": attachments
        },

        "saveToSentItems": True
    }

    # =========================================================
    # 6. Enviar mediante Microsoft Graph
    # =========================================================

    url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{correo_remitente}/sendMail"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json=mensaje,
        timeout=30
    )

    if response.status_code not in (200, 202):
        raise Exception(
            f"Error enviando correo mediante Microsoft Graph: "
            f"{response.status_code} - "
            f"{response.text}"
        )
def enviar_correo_nueva_solicitud(
    radicado,
    razon_social,
    nombre_remitente,
    correo_contacto,
    telefono_contacto,
    poliza,
    tipo_solicitud,
    descripcion
):

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    correo_remitente = os.getenv("MAIL_USERNAME")

    if not tenant_id:
        raise Exception("Falta TENANT_ID en las variables de entorno.")

    if not client_id:
        raise Exception("Falta CLIENT_ID en las variables de entorno.")

    if not client_secret:
        raise Exception("Falta CLIENT_SECRET en las variables de entorno.")

    # =========================================================
    # 1. Obtener token Microsoft Graph
    # =========================================================

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}/oauth2/v2.0/token"
    )

    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token_response = requests.post(
        token_url,
        data=token_data,
        timeout=20
    )

    if token_response.status_code != 200:
        raise Exception(
            f"Error obteniendo token Microsoft Graph: "
            f"{token_response.status_code} - "
            f"{token_response.text}"
        )

    access_token = token_response.json()["access_token"]

    # =========================================================
    # 2. Destinatarios
    # =========================================================

    destinatarios = [
        "tecnologiasvisuales940@gmail.com",
        "lider.estrategia@vivasegurosltda.com.co"
    ]

    # =========================================================
    # 3. Cuerpo del correo
    # =========================================================

    cuerpo = f"""
    NUEVA SOLICITUD RADICADA

    Radicado: {radicado}

    Razón Social: {razon_social}
    Nombre: {nombre_remitente}
    Correo: {correo_contacto}
    Teléfono: {telefono_contacto}
    Póliza: {poliza}
    Tipo: {tipo_solicitud}

    Descripción:
    {descripcion}
    """

    # =========================================================
    # 4. Construir destinatarios Graph
    # =========================================================

    to_recipients = []

    for correo in destinatarios:

        to_recipients.append({
            "emailAddress": {
                "address": correo
            }
        })

    # =========================================================
    # 5. Construir mensaje
    # =========================================================

    mensaje = {
        "message": {

            "subject": (
                f"{radicado} - "
                f"{tipo_solicitud} - "
                f"Póliza {poliza}"
            ),

            "body": {
                "contentType": "Text",
                "content": cuerpo
            },

            "toRecipients": to_recipients
        },

        "saveToSentItems": True
    }

    # =========================================================
    # 6. Enviar mediante Microsoft Graph
    # =========================================================

    url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{correo_remitente}/sendMail"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json=mensaje,
        timeout=30
    )

    if response.status_code not in (200, 202):

        raise Exception(
            f"Error enviando correo de nueva solicitud: "
            f"{response.status_code} - "
            f"{response.text}"
        )
def enviar_correo_recuperacion(
    correo,
    nombre,
    username,
    password_temporal
):

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    correo_remitente = os.getenv("MAIL_USERNAME")

    if not tenant_id:
        raise Exception("Falta TENANT_ID en las variables de entorno.")

    if not client_id:
        raise Exception("Falta CLIENT_ID en las variables de entorno.")

    if not client_secret:
        raise Exception("Falta CLIENT_SECRET en las variables de entorno.")

    if not correo_remitente:
        raise Exception("Falta MAIL_USERNAME en las variables de entorno.")

    # Obtener token Microsoft Graph

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}/oauth2/v2.0/token"
    )

    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token_response = requests.post(
        token_url,
        data=token_data,
        timeout=20
    )

    if token_response.status_code != 200:
        raise Exception(
            f"Error obteniendo token Microsoft Graph: "
            f"{token_response.status_code} - "
            f"{token_response.text}"
        )

    access_token = token_response.json()["access_token"]

    # Contenido del correo

    cuerpo = f"""
Hola {nombre},

Se generó una contraseña temporal para ingresar a VivaAP.

Usuario:
{username}

Contraseña temporal:
{password_temporal}

Una vez ingrese al sistema le recomendamos cambiarla inmediatamente.

Si usted no solicitó este cambio comuníquese con el administrador.

Equipo VivaAP
"""

    mensaje = {
        "message": {
            "subject": "Recuperación de contraseña - VivaAP",

            "body": {
                "contentType": "Text",
                "content": cuerpo
            },

            "toRecipients": [
                {
                    "emailAddress": {
                        "address": correo
                    }
                }
            ]
        },

        "saveToSentItems": True
    }

    url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{correo_remitente}/sendMail"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json=mensaje,
        timeout=30
    )

    if response.status_code not in (200, 202):
        raise Exception(
            f"Error enviando correo de recuperación: "
            f"{response.status_code} - "
            f"{response.text}"
        )