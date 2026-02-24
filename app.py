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
from flask_login import current_user

def solo_internos(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.rol != "interno":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_PATH, "uploads")

app = Flask(__name__)
app.secret_key = "vivaap_secret"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CORREO

app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tecnologiasvisuales940@gmail.com'
app.config['MAIL_PASSWORD'] = 'koavxwdwsdornvsv'
app.config['MAIL_DEFAULT_SENDER'] = 'tecnologiasvisuales940@gmail.com'

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

def get_db():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url)

class User(UserMixin):
    def __init__(self, id, username, rol):
        self.id = str(id)
        self.username = username
        self.rol = rol   # 🔥 ESTE CAMPO ES LA CLAVE

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, rol FROM usuarios WHERE id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return User(row[0], row[1], row[2])
    return None


def generar_radicado():
    return f"VIVAP-{datetime.now().year}-{random.randint(10000,99999)}"

# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, rol FROM usuarios WHERE username=%s", (u,))
        user = cur.fetchone()
        if user and check_password_hash(user[1], p):
            login_user(User(user[0], u, user[2]))
            return redirect('/panel')
    return render_template('login.html')

@app.route('/crear_usuario', methods=['GET','POST'])
@login_required
def crear_usuario():
    # Solo internos pueden crear usuarios
    if current_user.rol != "interno":
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

# FORMULARIO
@app.route('/')
@login_required
def form():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 🔹 Traer empleados para el select
    cur.execute("""
        SELECT id, nombre_completo 
        FROM usuarios 
        WHERE rol='interno' AND activo=TRUE
        ORDER BY nombre_completo
    """)
    empleados = cur.fetchall()

    rol = current_user.rol

    # 🔹 Filtros (solo si es interno/admin)
    estado_filtro = request.args.get('estado')
    usuario_filtro = request.args.get('usuario')

    if rol == "interno":   # 👑 TU USUARIO ADMIN
        query = """
            SELECT s.id, s.razon_social, s.nombre_remitente, 
                   s.tipo_solicitud, s.estado,
                   u.nombre_completo AS asignado_nombre
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

        query += " ORDER BY s.id DESC"

        cur.execute(query, params)

    else:
        # 👤 Usuario normal solo ve los suyos
        cur.execute("""
            SELECT s.id, s.razon_social, s.nombre_remitente, 
                   s.tipo_solicitud, s.estado,
                   u.nombre_completo AS asignado_nombre
            FROM solicitudes s
            LEFT JOIN usuarios u ON s.asignado_a = u.id
            WHERE s.asignado_a = %s
            ORDER BY s.id DESC
        """, (current_user.id,))

    solicitudes = cur.fetchall()

    conn.close()

    return render_template(
        'form.html',
        empleados=empleados,
        solicitudes=solicitudes,
        rol=rol
    )

# PANEL
@app.route('/panel')
@login_required
def panel():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Solicitudes
    cursor.execute("""
        SELECT s.*, u.nombre_completo AS asignado_nombre
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.asignado_a = u.id
        ORDER BY s.id DESC
    """)
    solicitudes = cursor.fetchall()

    # ===== CONTADORES =====
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
    # Empleados para el select
    cursor.execute("""
        SELECT id, nombre_completo
        FROM usuarios
        WHERE rol='interno' AND activo=TRUE
        ORDER BY nombre_completo
    """)
    empleados = cursor.fetchall()

    conn.close()

    return render_template(
    'panel.html',
    solicitudes=solicitudes,
    empleados=empleados,
    total=total,
    pendientes=pendientes,
    proceso=proceso,
    resueltos=resueltos,
    cerrados=cerrados
)


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
        telefono_contacto, poliza, tipo_solicitud, descripcion, asignado_a)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        asignado_a

    ))


    nuevo_id = cursor.fetchone()[0]

    # Crear radicado
    radicado = f"RAD-{nuevo_id:05d}"
    cursor.execute("UPDATE solicitudes SET radicado = %s WHERE id = %s", (radicado, nuevo_id))
    conn.commit()
    conn.close()

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


    # Adjuntar múltiples archivos desde memoria
    for archivo in request.files.getlist('archivos'):
        if archivo and archivo.filename:
            archivo.stream.seek(0)  # 🔥 RESETEA EL PUNTERO (CLAVE)
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(archivo.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={secure_filename(archivo.filename)}')
            msg.attach(part)

    # Enviar correo vía SMTP
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)

    flash(f"Solicitud enviada correctamente. Radicado: {radicado}")
    return redirect('/')

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
    if "RENDER" not in os.environ:  # solo local
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port, debug=True)
