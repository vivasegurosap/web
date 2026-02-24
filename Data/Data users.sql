CREATE TABLE usuarios (
    id INT IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    rol VARCHAR(30), -- Admin / Operador
    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE solicitudes (
    id INT IDENTITY PRIMARY KEY,
    radicado VARCHAR(30),
    fecha_creacion DATETIME DEFAULT GETDATE(),
    razon_social VARCHAR(150),
    nombre_remitente VARCHAR(100),
    correo_contacto VARCHAR(120),
    telefono_contacto VARCHAR(30),
    poliza VARCHAR(50),
    tipo_solicitud VARCHAR(50),
    descripcion TEXT,
    archivo VARCHAR(255),
    estado VARCHAR(30) DEFAULT 'Recibido',
    atendido_por VARCHAR(100),
    fecha_cierre DATETIME
);

INSERT INTO usuarios (username, password_hash, nombre_completo, rol)
VALUES (
'admin',
'PEGA_AQUI_EL_HASH',
'Administrador VivAP',
'Admin'
);

INSERT INTO usuarios (username, password_hash, nombre_completo, rol)
VALUES (
'admin',
'scrypt:32768:8:1$Xk39...algo_largo',
'Administrador VivAP',
'Admin'
);
UPDATE usuarios
SET password_hash = 'scrypt:32768:8:1$7Ucf3psNVTaSmzrb$ad5b94575cb435a9ec28bf2c1ff4adc66b317f44b6edb6c3c06a98628879143dfe2f95c5a7268911d6df32fb4a29965ec013d4a6550255bfff2ad69234096c62'
WHERE username = 'admin';

UPDATE usuarios
SET activo = 1
WHERE username = 'admin';

ALTER TABLE usuarios ADD rol VARCHAR(20);

select * from solicitudes
select * from usuarios
select * from EMPLOYEES

UPDATE usuarios
SET rol = 'interno'
WHERE id = 1;

UPDATE usuarios
SET rol = 'externo'
WHERE id = 2;

UPDATE usuarios
SET password_hash = 'scrypt:32768:8:1$A0ytGKHwO3nn2K0H$e22e542032af438b1e692756998ee46e1f8af23e0a15684b46707bea5ce6568b5a504a2f8466af178364a9567fe47d6e17edee55aa2b3940a3ac7dbb8b7edc22'
WHERE id = 2;


TRUNCATE TABLE solicitudes;

ALTER TABLE solicitudes
ADD asignado_a VARCHAR(100);

ALTER TABLE usuarios
ADD correo VARCHAR(150);

INSERT INTO usuarios
(username, password_hash, nombre_completo, rol, activo, fecha_creacion, correo)
VALUES

SELECT id, username, nombre_completo, rol, activo 
FROM usuarios

CREATE VIEW vw_solicitudes_completas AS
SELECT 
    s.id,
    s.razon_social,
    s.nombre_remitente,
    s.correo_contacto,
    s.telefono_contacto,
    s.poliza,
    s.tipo_solicitud,
    s.descripcion,
    u.nombre_completo AS asignado_a
FROM solicitudes s
LEFT JOIN usuarios u 
    ON s.asignado_a = u.id;

	SELECT * FROM vw_solicitudes_completas;

select * from usuarios