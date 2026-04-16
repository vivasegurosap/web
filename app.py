from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import random
import smtplib
import psycopg2
import psycopg2.extras
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from functools import wraps
from flask import abort
from flask import send_file
from io import BytesIO

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
ENV = os.environ.get("ENV", "dev") #se coloca por ahora para evitar el error cuando se envia el correo, dado que se cobra.
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CORREO

app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tecnologiasvisuales940@gmail.com'
app.config['MAIL_PASSWORD'] = 'koavxwdwsdornvsv'
app.config['MAIL_DEFAULT_SENDER'] = 'tecnologiasvisuales940@gmail.com'
mail = Mail(app)

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL no está configurado")

    # 🔥 Render a veces usa postgres:// y psycopg2 exige postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(database_url)

class User(UserMixin):
    def __init__(self, id, username, rol, nombre_completo):
        self.id = str(id)
        self.username = username
        self.rol = rol
        self.nombre_completo = nombre_completo

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, rol, nombre_completo 
        FROM usuarios 
        WHERE id=%s
    """, (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return User(row[0], row[1], row[2], row[3])
    return None


def generar_radicado():
    return f"VIVAP-{datetime.now().year}-{random.randint(10000,99999)}"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, username, rol, nombre_completo, password_hash
            FROM usuarios
            WHERE username=%s AND activo=TRUE
        """, (u,))

        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[4], p):
            login_user(User(user[0], user[1], user[2], user[3]))
            flash("modal_bienvenida")
            return redirect('/panel')

    return render_template('login.html')

@app.route('/crear_usuario', methods=['GET','POST'])
@login_required
def crear_usuario():
    # Solo internos pueden crear usuarios
    if current_user.rol not in ["interno", "admin"]:
        abort(403)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre = request.form['nombre']
        rol = request.form['rol']

        password_hash = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, rol, activo, fecha_creacion)
            VALUES (%s, %s, %s, %s, TRUE, NOW())
        """, (username, password_hash, nombre, rol))


        conn.commit()
        conn.close()

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

# PANEL
@app.route('/panel')
@login_required
def panel():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    estado_filtro = request.args.get("estado")
    usuario_filtro = request.args.get("usuario")
    empresa_filtro = request.args.get("empresa")
    page = request.args.get("page", 1, type=int)
    per_page = 7
    offset = (page - 1) * per_page
    
# 🔹 TRAER SIEMPRE LOS USUARIOS INTERNOS (para el select "Asignar a")
    cursor.execute("""
        SELECT id, nombre_completo
        FROM usuarios
        WHERE rol = 'interno'
        AND activo = TRUE
        ORDER BY nombre_completo
    """)
    empleados = cursor.fetchall()
    cursor.execute("""
        SELECT DISTINCT razon_social 
        FROM solicitudes
        ORDER BY razon_social
    """)
    empresas = cursor.fetchall()

    # 🔴 ADMIN VE TODO
    if current_user.rol == "admin":

        query = """
            SELECT s.*, u.nombre_completo AS asignado_nombre
            FROM solicitudes s
            LEFT JOIN usuarios u ON s.asignado_a = u.id
            WHERE 1=1
        """
        params = []

        if estado_filtro:
            query += " AND s.estado = %s"
            params.append(estado_filtro)

        if usuario_filtro:
            query += " AND s.asignado_a = %s"
            params.append(usuario_filtro)

        query += " ORDER BY s.id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)

        solicitudes = cursor.fetchall()
        tiene_siguiente = len(solicitudes) == per_page

        cursor.execute("SELECT COUNT(*) FROM solicitudes")
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Pendiente'")
        pendientes = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='En proceso'")
        proceso = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Resuelto'")
        resueltos = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Cerrado'")
        cerrados = cursor.fetchone()['count']

    # 🔵 INTERNO SOLO VE LO ASIGNADO A ÉL
    elif current_user.rol == "interno":

        query = """
            SELECT s.*, u.nombre_completo AS asignado_nombre
            FROM solicitudes s
            LEFT JOIN usuarios u ON s.asignado_a = u.id
            WHERE s.asignado_a = %s
        """
        params = [current_user.id]

        if estado_filtro:
            query += " AND s.estado = %s"
            params.append(estado_filtro)
        if empresa_filtro:
            query += " AND s.razon_social ILIKE %s"
            params.append(f"%{empresa_filtro}%")

        query += " ORDER BY s.id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        solicitudes = cursor.fetchall()
        tiene_siguiente = len(solicitudes) == per_page

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE asignado_a=%s", (current_user.id,))
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Pendiente' AND asignado_a=%s", (current_user.id,))
        pendientes = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='En proceso' AND asignado_a=%s", (current_user.id,))
        proceso = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Resuelto' AND asignado_a=%s", (current_user.id,))
        resueltos = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Cerrado' AND asignado_a=%s", (current_user.id,))
        cerrados = cursor.fetchone()['count']

    # 🟢 EXTERNO SOLO VE LO QUE ÉL RADICÓ
    else:

        query = """
            SELECT s.*, u.nombre_completo AS asignado_nombre
            FROM solicitudes s
            LEFT JOIN usuarios u ON s.asignado_a = u.id
            WHERE s.creado_por = %s
        """
        params = [current_user.id]

        if estado_filtro:
            query += " AND s.estado = %s"
            params.append(estado_filtro)

        query += " ORDER BY s.id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        solicitudes = cursor.fetchall()
        tiene_siguiente = len(solicitudes) == per_page

        cursor.execute("""
            SELECT COUNT(*) FROM solicitudes 
            WHERE creado_por = %s
        """, (current_user.id,))
        total = cursor.fetchone()['count']

        pendientes = proceso = resueltos = cerrados = 0

    conn.close()

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
        tiene_siguiente=tiene_siguiente
    )
# ruta para ver el caso
@app.route('/solicitud/<int:id>')
@login_required
def ver_solicitud(id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT s.*, u.nombre_completo AS asignado_nombre
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.asignado_a = u.id
        WHERE s.id = %s
    """, (id,))

    solicitud = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM archivos
        WHERE solicitud_id = %s
    """, (id,))

    archivos = cursor.fetchall()

    conn.close()

    return render_template(
        "detalle_solicitud.html",
        solicitud=solicitud,
        archivos=archivos
    )

@app.route('/descargar/<int:id>')
@login_required
def descargar_archivo(id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT nombre_archivo, tipo_archivo, archivo
        FROM archivos
        WHERE id = %s
    """, (id,))

    archivo = cursor.fetchone()
    conn.close()

    if not archivo:
        abort(404)

    from io import BytesIO

    return send_file(
        BytesIO(archivo['archivo']),
        download_name=archivo['nombre_archivo'],
        mimetype=archivo['tipo_archivo'],
        as_attachment=True
    )
#ruta para eliminar los radicado.
@app.route('/eliminar_solicitud/<int:id>')
@login_required
def eliminar_solicitud(id):

    if current_user.rol != "admin":
        return "No autorizado", 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM solicitudes WHERE id = %s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Solicitud eliminada correctamente")

    return redirect("/panel")


@app.route('/crear_solicitud', methods=['POST'])
@login_required
def crear_solicitud():
    conn = get_db()
    cursor = conn.cursor()

    # VALIDACIÓN SEGURA DE ASIGNADO_A
    try:
        asignado_a = int(request.form.get("asignado_a"))
    except (TypeError, ValueError):
        flash("Debe seleccionar un empleado válido")
        conn.close()
        return redirect(url_for("panel"))


    # Guardar solicitud en la base de datos
    cursor.execute("""
        INSERT INTO solicitudes
        (razon_social, nombre_remitente, correo_contacto,
        telefono_contacto, poliza, tipo_solicitud, descripcion, asignado_a, creado_por)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """,
    (
        request.form['razon_social'],
        request.form['nombre_remitente'],
        request.form['correo_contacto'],
        request.form['telefono_contacto'],
        request.form['poliza'],
        request.form['tipo_solicitud'],
        request.form['descripcion'],
        asignado_a,
        current_user.id
    ))


    nuevo_id = cursor.fetchone()[0]

    # Crear radicado
    radicado = f"RAD-{nuevo_id:05d}"
    cursor.execute("UPDATE solicitudes SET radicado = %s WHERE id = %s", (radicado, nuevo_id))
    
    # --- Crear mensaje
    
    msg = MIMEMultipart()
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = "tecnologiasvisuales940@gmail.com, lider.estrategia@vivasegurosltda.com.co"
    msg['Subject'] = f"{radicado} - {request.form['tipo_solicitud']} - Póliza {request.form['poliza']}"

    # Cuerpo del correo con UTF-8
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
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    # Adjuntar múltiples archivos
    for archivo in request.files.getlist('archivos'):
        if archivo and archivo.filename:
            nombre = secure_filename(archivo.filename)
            tipo = archivo.content_type
            contenido = archivo.read()
            cursor.execute("""
                INSERT INTO archivos (solicitud_id, nombre_archivo, tipo_archivo, archivo)
                VALUES (%s,%s,%s,%s)
            """, (nuevo_id, nombre, tipo, contenido))

    conn.commit()
    conn.close()

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
@app.route('/estado/<int:id>/<estado>')
@login_required
@solo_internos   # 🔒 SOLO INTERNOS PUEDEN CAMBIAR ESTADO
def estado(id, estado):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE solicitudes 
        SET estado=%s, atendido_por=%s 
        WHERE id=%s
    """, (estado, current_user.username, id))


    if estado == "Cerrado":
        cur.execute("UPDATE solicitudes SET fecha_cierre=NOW() WHERE id=%s", (id,))

    conn.commit()
    conn.close()
    return redirect('/panel')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)