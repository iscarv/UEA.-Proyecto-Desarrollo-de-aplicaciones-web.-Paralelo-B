--Script

-- -----------------------------
-- Crear tabla usuarios
-- -----------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password TEXT NOT NULL
);


-- -----------------------------
-- Crear tabla productos
-- -----------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    autor VARCHAR(255) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    cantidad INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    portada VARCHAR(255)
);


-- -----------------------------
-- Crear tabla pedidos
-- -----------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
);

-- -----------------------------
-- Insertar datos en usuarios
-- -----------------------------
INSERT INTO usuarios (nombre, email) VALUES
('Juan Pérez', 'juan@example.com'),
('María López', 'maria@example.com'),
('Carlos Sánchez', 'carlos@example.com'),
('Rosa Castillo', 'rosa@example.com');

-- =============================
--Actualizar contraseñas en usuarios existentes con contraseñas encriptadas
-- Las contraseñas en texto plano serían:
--   juan123  
--   maria123 
--   carlos123 
--Los hashes fueron generados con Werkzeug (generate_password_hash)
-- =============================
UPDATE usuarios
SET password = 'scrypt:32768:8:1$MgBMFI5Z3eGmdWRG$4ed7d1136ec1c378ec70a506601de30d91143676fc54af1ed06bc57423cf31094a78f59616f175adc5b44182ea9014249e1b1dac648ad360a4316bdaf2c8dc40'
WHERE id_usuario = 1;

UPDATE usuarios
SET password = 'scrypt:32768:8:1$s57oTSe8lcyYkqLv$b838d368adb5d9ee5af29959e7f1d326a242247e16571ef3c1ba9ca2e4cfc6fdaf8112c39ab1ef6a193e14d2acaf0a1d5dfec4594843e7fb05d540c323e69b43'
WHERE id_usuario = 2;

UPDATE usuarios
SET password = 'scrypt:32768:8:1$4EyGBNfLcQq5a7MI$86aef9173c0084bf70e010f39ffeaf2e8e947e97db8cbe4218f8b93ea29b77cf057706b1cb2525d63726730e921943accebeadfb9ef8ef8552d9f910f9e278f0'
WHERE id_usuario = 3;

UPDATE usuarios
SET password = 'scrypt:32768:8:1$y5ptKnDBKGn02d7H$46c241247067fbfb6039ffa9f945cb67248624a1aef61ac665d654aae72ac0040803bdd42eb472b21802c3b7b7442dee0c00d72d1ef61c65f08b84ef37f4ea9f'
WHERE id_usuario = 4;


-- -----------------------------
-- Insertar datos en productos
-- -----------------------------
INSERT INTO productos (titulo, autor, categoria, cantidad, precio, portada)
VALUES 
('Los Miserables', 'Victor Hugo', 'Ficción Histórica', 13, 19.99, NULL),
('Guerra y Paz', 'León Tolstói', 'Novela', 20, 22.00, NULL);


-- -----------------------------
-- Insertar datos en pedidos
-- -----------------------------
INSERT INTO pedidos (id_usuario, id_producto, cantidad, fecha_pedido)
VALUES
(1, 1, 1, '2025-09-11'),  -- Juan pide "Los Miserables"
(2, 2, 2, '2025-09-11');  -- María pide "Guerra y Paz"