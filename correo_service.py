from flask_mail import Message
from flask import current_app
from pathlib import Path

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
def enviar_correo_resolucion(mail, solicitud, html, adjuntos=None):
    msg = Message(
        subject=f"Respuesta a la solicitud {solicitud['radicado']}",
        recipients=[solicitud["correo_contacto"]]
    )
    msg.html = html

    # Logo embebido
    logo = Path(current_app.root_path) / "static" / "VivaSeguros_Logo2025_Blanco.png"
    with open(logo, "rb") as f:
        msg.attach(
            filename="VivaSeguros_Logo2025_Blanco.png",
            content_type="image/png",
            data=f.read(),
            disposition="inline",
            headers={
                "Content-ID": "<logo_viva>"
            }
        )
    if adjuntos:
        for archivo in adjuntos:
            msg.attach(
                archivo["nombre"],
                archivo["mime"],
                archivo["contenido"]
            )
    mail.send(msg)