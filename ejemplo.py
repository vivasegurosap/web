from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.office365.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='vivap.notificaciones@outlook.com',
    MAIL_PASSWORD='nrglivfcsbocnhsr',
    MAIL_DEFAULT_SENDER='vivap.notificaciones@outlook.com'
)
mail = Mail(app)

with app.app_context():
    msg = Message("Prueba de correo", recipients=["tu_correo@ejemplo.com"])
    msg.body = "Hola, esto es una prueba."
    mail.send(msg)
    print("Correo enviado correctamente")
