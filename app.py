from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import random
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from functools import wraps
from flask import abort
from flask import send_file
from io import BytesIO
import pandas as pd
from sharepoint_service import (crear_solicitud_sharepoint, obtener_siguiente_radicado, obtener_usuarios_internos)
from sharepoint_service import obtener_solicitudes
from sharepoint_service import crear_item_sharepoint
from sharepoint_service import obtener_usuario_por_id
from sharepoint_service import obtener_token
from sharepoint_service import eliminar_item_sharepoint
from sharepoint_service import actualizar_item_sharepoint
from usuarios_sharepoint import (buscar_usuario_por_correo, actualizar_password_usuario, buscar_usuario)
from correo_service import crear_html_resolucion, enviar_correo_resolucion
from sharepoint_service import obtener_adjuntos_para_correo
import secrets
import string
import re

def solo_internos(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ["interno", "admin"]:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

#BASE_PATH = os.path.dirname(os.path.abspath(__file__))
#UPLOAD_FOLDER = os.path.join(BASE_PATH, "uploads")

app = Flask(__name__)
app.secret_key = "vivaap_secret"
LISTA_USUARIOS_ID = os.getenv("USUARIOS_LIST_ID")
LISTA_SOLICITUDES_ID = os.getenv("LIST_ID")
ENV = os.environ.get("ENV", "dev") #se coloca por ahora para evitar el error cuando se envia el correo, dado que se cobra.
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CORREO
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tecnologiasvisuales940@gmail.com'
app.config['MAIL_PASSWORD'] = 'koavxwdwsdornvsv'
app.config['MAIL_DEFAULT_SENDER'] = 'tecnologiasvisuales940@gmail.com'
mail = Mail(app)

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, rol, nombre_completo):
        self.id = str(id)
        self.username = username
        self.rol = rol
        self.nombre_completo = nombre_completo

def generar_password_temporal():

    letras = string.ascii_letters
    numeros = string.digits

    caracteres = letras + numeros

    return "".join(
        random.choice(caracteres)
        for _ in range(10)
    )
@login_manager.user_loader
def load_user(user_id):

    from usuarios_sharepoint import buscar_usuario_por_id

    user = buscar_usuario_por_id(user_id)

    if user:
        return User(
            user["id"],
            user["username"],
            user["rol"],
            user["nombre_completo"]
        )

    return None


def generar_radicado():
    return f"VIVAP-{datetime.now().year}-{random.randint(10000,99999)}"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']

        from usuarios_sharepoint import buscar_usuario
        user = buscar_usuario(u)

        print("USUARIO:", user)
        print("PASSWORD TEMPORAL:", user.get("password_temporal"))

        if user:

            resultado = check_password_hash(user["password_hash"], p)

            print("PASSWORD OK:", resultado)

            if resultado:

                login_user(User(
                    user["id"],
                    user["username"],
                    user["rol"],
                    user["nombre_completo"]
                ))

                # Si la contraseña es temporal
                if user.get("password_temporal"):

                    return redirect(url_for("cambiar_password_temporal"))

                flash("modal_bienvenida")
                return redirect("/panel")

            else:
                flash("Usuario o contraseña incorrecta.")

        else:
            flash("Usuario o contraseña incorrecta.")

    return render_template('login.html') 

@app.route("/recuperar_password", methods=["GET", "POST"])
def recuperar_password():

    if request.method == "POST":

        correo = request.form["correo"].strip().lower()

        from usuarios_sharepoint import (
            buscar_usuario_por_correo,
            actualizar_password_usuario
        )

        from werkzeug.security import generate_password_hash

        usuario = buscar_usuario_por_correo(correo)

        if usuario:

            try:

                # Generar contraseña temporal
                password_temporal = generar_password_temporal()

                # Convertir a hash
                password_hash = generate_password_hash(password_temporal)

                # Actualizar SharePoint
                actualizar_password_usuario(
                    usuario["id"],
                    password_hash,
                    True
                )

                # Enviar correo
                msg = Message(
                    subject="Recuperación de contraseña - VivaAP",
                    recipients=[correo]
                )

                msg.body = f"""
        Hola {usuario['nombre_completo']},

        Se generó una contraseña temporal para ingresar a VivaAP.

        Usuario:
        {usuario['username']}

        Contraseña temporal:
        {password_temporal}

        Una vez ingrese al sistema le recomendamos cambiarla inmediatamente.

        Si usted no solicitó este cambio comuníquese con el administrador.

        Equipo VivaAP
        """

                mail.send(msg)
                print("CONTRASEÑA TEMPORAL:", password_temporal)

            except Exception as e:

                print("ERROR RECUPERAR PASSWORD:", e)

                flash("Ocurrió un error al generar la contraseña temporal.")

                return redirect(url_for("recuperar_password"))

        flash("Si el correo existe en el sistema, recibirá una contraseña temporal para ingresar a VivaAP.")

        return redirect(url_for("login"))

    return render_template("recuperar_password.html")  

@app.route("/cambiar_password_temporal", methods=["GET","POST"])
@login_required
def cambiar_password_temporal():
    from usuarios_sharepoint import buscar_usuario_por_id

    usuario = buscar_usuario_por_id(current_user.id)

    if not usuario.get("password_temporal"):

        return redirect(url_for("panel"))
    if request.method == "POST":

        nueva = request.form["password"]

        confirmar = request.form["confirmar"]

        if nueva != confirmar:

            flash("Las contraseñas no coinciden.")

            return redirect(
                url_for("cambiar_password_temporal")
            )
        
        # Validaciones de seguridad
        if len(nueva) < 8:
            flash("La contraseña debe tener mínimo 8 caracteres.")
            return redirect(url_for("cambiar_password_temporal"))

        if not re.search(r"[A-Z]", nueva):
            flash("La contraseña debe contener al menos una letra mayúscula.")
            return redirect(url_for("cambiar_password_temporal"))

        if not re.search(r"[0-9]", nueva):
            flash("La contraseña debe contener al menos un número.")
            return redirect(url_for("cambiar_password_temporal"))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', nueva):
            flash("La contraseña debe contener al menos un carácter especial.")
            return redirect(url_for("cambiar_password_temporal"))

        password_hash = generate_password_hash(nueva)

        from usuarios_sharepoint import actualizar_password_definitiva

        actualizar_password_definitiva(
            current_user.id,
            password_hash
        )

        logout_user()

        flash("Contraseña actualizada correctamente. Inicie sesión con su nueva contraseña.")

        return redirect(url_for("login"))

    return render_template("cambiar_password.html")

@app.route('/crear_usuario', methods=['GET','POST'])
@login_required
def crear_usuario():

    if current_user.rol not in ["interno", "admin"]:
        abort(403)

    if request.method == 'POST':

        username = request.form['username'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip().lower()
        password = request.form['password']
        rol = request.form['rol']

        # Validar usuario existente
        if buscar_usuario(username):
            flash("El nombre de usuario ya existe.")
            return render_template("crear_usuario.html")

        # Validar correo existente
        if buscar_usuario_por_correo(correo):
            flash("El correo ya se encuentra registrado.")
            return render_template("crear_usuario.html")

        password_hash = generate_password_hash(password)

        datos = {
            "Username": username,
            "NombreCompleto": nombre,
            "Correo": correo,
            "Rol": rol,
            "Activo": True,
            "PasswordHash": password_hash,
            "FechaCreacion": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        crear_item_sharepoint(LISTA_USUARIOS_ID, datos)

        flash("Usuario creado correctamente")
        return redirect('/panel')

    return render_template('crear_usuario.html')

# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def home():
    return redirect(url_for('panel'))

@app.route('/exportar_excel')
@login_required
def exportar_excel():

    from sharepoint_service import obtener_solicitudes

    estado = request.args.get("estado")
    usuario = request.args.get("usuario")
    q = request.args.get("q")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    solicitudes = obtener_solicitudes()

    # Filtrar por rol

    if current_user.rol == "interno":
        solicitudes = [
            s for s in solicitudes
            if s["asignado_a"] == str(current_user.id)
        ]

    elif current_user.rol == "externo":
        solicitudes = [
            s for s in solicitudes
            if s["creado_por"] == str(current_user.id)
        ]
    # Filtro estado

    if estado:
        solicitudes = [
            s for s in solicitudes
            if s.get("estado") == estado
        ]
    # Filtro usuario

    if usuario:
        solicitudes = [
            s for s in solicitudes
            if str(s.get("asignado_a")) == str(usuario)
        ]
    # Filtro por fechas
    if fecha_inicio:
        fecha_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()

        solicitudes = [
            s for s in solicitudes
            if s.get("fecha_creacion")
            and s["fecha_creacion"].date() >= fecha_ini
        ]

    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        solicitudes = [
            s for s in solicitudes
            if s.get("fecha_creacion")
            and s["fecha_creacion"].date() <= fecha_fin_dt
        ]

    # Filtro búsqueda

    if q:

        q = q.lower()

        solicitudes = [

            s for s in solicitudes

            if q in str(s.get("radicado", "")).lower()
            or q in str(s.get("razon_social", "")).lower()
            or q in str(s.get("nombre_remitente", "")).lower()
            or q in str(s.get("tipo_solicitud", "")).lower()

        ]

    if not solicitudes:

        flash("No hay datos para exportar")
        return redirect(url_for('panel'))

    datos_excel = []

    for s in solicitudes:

        usuario = obtener_usuario_por_id(
            s.get("asignado_a")
        )

        nombre_asignado = ""

        if usuario:
            nombre_asignado = usuario.get(
                "nombre_completo"
            )

        datos_excel.append({

            "Radicado": s.get("radicado"),
            "Empresa": s.get("razon_social"),
            "Solicitante": s.get("nombre_remitente"),
            "Tipo Solicitud": s.get("tipo_solicitud"),
            "Estado": s.get("estado"),
            "Asignado A": nombre_asignado,
            "Fecha Creación": s.get("fecha_creacion"),
            "Fecha Cierre": s.get("fecha_cierre")

        })

    df = pd.DataFrame(datos_excel)

    # Quitar timezone para Excel

    if 'Fecha Creación' in df.columns:
        df['Fecha Creación'] = pd.to_datetime(
            df['Fecha Creación'],
            errors='coerce'
        ).dt.tz_localize(None)

    if 'Fecha Cierre' in df.columns:
        df['Fecha Cierre'] = pd.to_datetime(
            df['Fecha Cierre'],
            errors='coerce'
        ).dt.tz_localize(None)

    output = BytesIO()

    df.to_excel(
        output,
        index=False,
        engine="openpyxl"
    )

    output.seek(0)

    return send_file(
        output,
        download_name="reporte_solicitudes.xlsx",
        as_attachment=True
    )

# PANEL
@app.route('/panel')
@login_required
def panel():
    estado_filtro = request.args.get("estado")
    usuario_filtro = request.args.get("usuario")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q")
    per_page = 7
    offset = (page - 1) * per_page

    # 👇 AQUÍ VA LO NUEVO (SharePoint)
    from sharepoint_service import obtener_solicitudes, contar_solicitudes

    all_solicitudes = obtener_solicitudes()
    solicitudes = all_solicitudes

    if current_user.rol == "interno":
        solicitudes = [s for s in solicitudes if s["asignado_a"] == str(current_user.id)]

    elif current_user.rol == "externo":
        solicitudes = [s for s in solicitudes if s["creado_por"] == str(current_user.id)]

    if estado_filtro:
        solicitudes = [s for s in solicitudes if s.get("estado") == estado_filtro]

    if q:
        q = q.lower()
        solicitudes = [
            s for s in solicitudes
            if q in str(s.get("radicado", "")).lower()
            or q in str(s.get("razon_social", "")).lower()
            or q in str(s.get("nombre_remitente", "")).lower()
            or q in str(s.get("tipo_solicitud", "")).lower()
        ]
    # Filtro por usuario asignado
    if usuario_filtro:
        solicitudes = [
            s for s in solicitudes
            if str(s.get("asignado_a")) == str(usuario_filtro)
        ]

    # Filtro por rango de fechas
    if fecha_inicio:
        fecha_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()

        solicitudes = [
            s for s in solicitudes
            if s.get("fecha_creacion")
            and s["fecha_creacion"].date() >= fecha_ini
        ]

    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        solicitudes = [
            s for s in solicitudes
            if s.get("fecha_creacion")
            and s["fecha_creacion"].date() <= fecha_fin_dt
        ]

    # Datos temporales mientras terminamos la migración

    from sharepoint_service import obtener_usuarios_internos
    empleados = obtener_usuarios_internos()
    empresas = []

    total = len(solicitudes)

    pendientes = len([s for s in solicitudes if s.get("estado") == "Pendiente"])
    proceso = len([s for s in solicitudes if s.get("estado") == "En proceso"])
    resueltos = len([s for s in solicitudes if s.get("estado") == "Resuelto"])
    cerrados = len([s for s in solicitudes if s.get("estado") == "Cerrado"])

    inicio = offset
    fin = offset + per_page

    total_registros = len(solicitudes)
    total_paginas = (total_registros + per_page - 1) // per_page

    tiene_siguiente = page < total_paginas

    # Determinar qué páginas mostrar
    inicio_paginas = max(1, page - 2)
    fin_paginas = min(total_paginas, inicio_paginas + 4)

    # Si estamos al final, completar hasta mostrar 5 páginas
    inicio_paginas = max(1, fin_paginas - 4)

    paginas = list(range(inicio_paginas, fin_paginas + 1))

    solicitudes = solicitudes[inicio:fin]

    return render_template(
            'panel.html',
            solicitudes=solicitudes,
            total=total,
            pendientes=pendientes,
            proceso=proceso,
            resueltos=resueltos,
            cerrados=cerrados,
            empleados=empleados,
            empresas=empresas,
            page=page,
            tiene_siguiente=tiene_siguiente,
            total_paginas=total_paginas,
            paginas=paginas
    )

@app.route('/reasignar/<int:id>/<int:usuario_id>')
@login_required
def reasignar(id, usuario_id):

    volver = request.args.get("next", url_for("panel"))

    if current_user.rol not in ["admin", "interno"]:
        return redirect(volver)

    usuario = obtener_usuario_por_id(usuario_id)

    if not usuario:
        flash("Usuario no encontrado")
        return redirect(volver)

    actualizar_item_sharepoint(
        LISTA_SOLICITUDES_ID,
        id,
        {
            "AsignadoA": usuario["id"]
        }
    )

    flash("Solicitud reasignada correctamente")

    return redirect(volver)

# ruta para ver el caso
@app.route('/solicitud/<id>')
@login_required
def ver_solicitud(id):

    from sharepoint_service import (
        obtener_solicitud_por_id,
        obtener_adjuntos_solicitud
    )

    solicitud = obtener_solicitud_por_id(id)

    archivos = obtener_adjuntos_solicitud(
        solicitud["radicado"]
    )

    # URL desde donde llegó el usuario
    volver = request.args.get(
        "next",
        url_for("panel")
    )

    return render_template(
        "detalle_solicitud.html",
        solicitud=solicitud,
        archivos=archivos,
        volver=volver
    )

@app.route('/adjuntar_archivos/<id>', methods=['POST'])
@login_required
def adjuntar_archivos(id):
    volver = request.form.get("next", url_for("panel"))

    from sharepoint_service import (
        obtener_solicitud_por_id,
        subir_adjunto
    )

    solicitud = obtener_solicitud_por_id(id)

    archivos = request.files.getlist("archivos")

    for archivo in archivos:

        if archivo and archivo.filename:

            try:
                subir_adjunto(
                    solicitud["radicado"],
                    archivo
                )

            except Exception as e:
                print("ERROR SUBIENDO:", e)

    flash("Archivos agregados correctamente")

    return redirect(url_for("ver_solicitud", id=id, next=volver))

#ruta para eliminar los radicado.
@app.route('/eliminar_solicitud/<int:id>')
@login_required
def eliminar_solicitud(id):

    volver = request.args.get("next", url_for("panel"))

    if current_user.rol != "admin":
        return redirect(volver)

    try:

        eliminar_item_sharepoint(
            LISTA_SOLICITUDES_ID,
            id
        )

        flash("Solicitud eliminada correctamente")

    except Exception as e:

        print(e)

        flash("No fue posible eliminar la solicitud")

    return redirect(volver)

@app.route('/crear_solicitud', methods=['POST'])
@login_required
def crear_solicitud():
    try:
        asignado_a = int(request.form.get("asignado_a"))
    except (TypeError, ValueError):
        flash("Debe seleccionar un empleado válido")
        return redirect(url_for("panel"))
    from sharepoint_service import (
        obtener_siguiente_radicado,
        crear_carpeta_radicado,
        subir_adjunto
    )

    radicado = obtener_siguiente_radicado()
        # Crear mensaje de correo
    msg = MIMEMultipart()

    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = (
        "tecnologiasvisuales940@gmail.com,"
        "lider.estrategia@vivasegurosltda.com.co"
    )

    msg['Subject'] = (
        f"{radicado} - "
        f"{request.form['tipo_solicitud']} - "
        f"Póliza {request.form['poliza']}"
    )

    cuerpo = f"""
    NUEVA SOLICITUD RADICADA

    Radicado: {radicado}

    Razón Social: {request.form['razon_social']}
    Nombre: {request.form['nombre_remitente']}
    Correo: {request.form['correo_contacto']}
    Teléfono: {request.form['telefono_contacto']}
    Póliza: {request.form['poliza']}
    Tipo: {request.form['tipo_solicitud']}

    Descripción:
    {request.form['descripcion']}
    """

    msg.attach(
        MIMEText(cuerpo, 'plain', 'utf-8')
    )
    try:

        status, item_id = crear_solicitud_sharepoint(
            radicado=radicado,
            razon_social=request.form['razon_social'],
            nombre_remitente=request.form['nombre_remitente'],
            correo_contacto=request.form['correo_contacto'],
            telefono_contacto=request.form['telefono_contacto'],
            poliza=request.form['poliza'],
            tipo_solicitud=request.form['tipo_solicitud'],
            descripcion=request.form['descripcion'],
            asignado_a=str(asignado_a),
            creado_por=str(current_user.id)
        )
        # Crear carpeta del radicado
        crear_carpeta_radicado(radicado)

        print("STATUS SHAREPOINT:", status)

        from sharepoint_service import subir_adjunto

        archivos = request.files.getlist("archivos")

        for archivo in archivos:

            if archivo and archivo.filename:

                try:
                    subir_adjunto(radicado, archivo)

                except Exception as e:
                    print("ERROR SUBIENDO ARCHIVO:", e)

    except Exception as e:
        print("ERROR SHAREPOINT:", e)

    # Enviar correo SIN romper el sistema
    try:
        if ENV != "prod":
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
                server.starttls()
                server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                server.send_message(msg)
    except Exception as e:
        print("Error enviando correo:", e)

    # ✅ ESTO SIEMPRE DEBE EJECUTARSE
    flash(f"Solicitud enviada correctamente. Radicado: {radicado}")
    return redirect(url_for('panel'))

# CAMBIAR ESTADO
@app.route('/estado/<id>/<estado>')
@login_required
@solo_internos
def estado(id, estado):
    volver = request.args.get("next", url_for("panel"))

    from sharepoint_service import actualizar_estado_solicitud

    try:

        actualizar_estado_solicitud(
            item_id=id,
            nuevo_estado=estado,
            atendido_por=current_user.username
        )

        flash("Estado actualizado correctamente")

    except Exception as e:
        print("ERROR ACTUALIZANDO ESTADO:", e)
        flash("No fue posible actualizar el estado")

    return redirect(volver)

@app.route('/resolver/<int:id>', methods=["POST"])
@login_required
@solo_internos
def resolver_solicitud(id):

    from sharepoint_service import (
        obtener_solicitud_por_id,
        subir_adjunto,
        actualizar_estado_solicitud,
        obtener_adjuntos_para_correo
    )

    respuesta = request.form.get("respuesta", "").strip()
    sin_adjuntos = request.form.get("sinAdjuntos")
    archivos = request.files.getlist("archivos")

    # Validar que exista al menos un archivo o se marque la opción
    if not sin_adjuntos:

        archivos_validos = [a for a in archivos if a and a.filename]

        if len(archivos_validos) == 0:

            flash("Debe adjuntar al menos un archivo o marcar que la respuesta no requiere adjuntos.")

            return redirect(url_for("ver_solicitud", id=id))

    solicitud = obtener_solicitud_por_id(id)

    # Subir archivos a SharePoint
    if not sin_adjuntos:

        for archivo in archivos:

            if archivo and archivo.filename:

                subir_adjunto(
                    solicitud["radicado"],
                    archivo
                )

    # Cambiar estado
    actualizar_estado_solicitud(
        item_id=id,
        nuevo_estado="Resuelto",
        atendido_por=current_user.username
    )

    # Crear correo
    html = crear_html_resolucion(
        solicitud,
        respuesta
    )

    # Adjuntos para correo
    if sin_adjuntos:
        adjuntos = []
    else:
        adjuntos = obtener_adjuntos_para_correo(
            solicitud["radicado"]
        )

    # Enviar correo
    try:

        enviar_correo_resolucion(
            mail,
            solicitud,
            html,
            adjuntos
        )

        flash("Solicitud resuelta y correo enviado correctamente.")

    except Exception as e:

        print("ERROR ENVIANDO CORREO:", e)

        flash("La solicitud fue resuelta, pero ocurrió un error al enviar el correo.")

    return redirect(url_for("ver_solicitud", id=id))


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

    