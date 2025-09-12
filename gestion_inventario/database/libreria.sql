--Script

-- -----------------------------
-- Crear tabla usuarios
-- -----------------------------
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL
);

-- -----------------------------
-- Crear tabla productos
-- -----------------------------
CREATE TABLE productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    autor VARCHAR(100),
    categoria VARCHAR(50),
    cantidad INT DEFAULT 0,
    precio DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(255),       -- breve descripción del libro
    sinopsis TEXT                  -- sinopsis completa del libro
);

-- -----------------------------
-- Crear tabla pedidos
-- -----------------------------
CREATE TABLE pedidos (
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
('Carlos Sánchez', 'carlos@example.com');

-- -----------------------------
-- Insertar datos en productos
-- -----------------------------
INSERT INTO productos (titulo, autor, categoria, cantidad, precio, descripcion, sinopsis)
VALUES 
('Cien Años de Soledad', 'Gabriel García Márquez', 'Novela', 10, 25.99, 
 'Clásico de la literatura latinoamericana', 
 'La historia de la familia Buendía a lo largo de siete generaciones en Macondo.'),
('El Principito', 'Antoine de Saint-Exupéry', 'Infantil', 15, 15.50,
 'Libro para todas las edades', 
 'Un pequeño príncipe viaja por distintos planetas y aprende sobre la vida y la amistad.'),
('1984', 'George Orwell', 'Distopía', 8, 20.00,
 'Novela distópica', 
 'Una sociedad totalitaria donde el Gran Hermano controla todo y la libertad es inexistente.'),
('Orgullo y Prejuicio', 'Jane Austen', 'Romance', 12, 18.75,
 'Clásico del romanticismo inglés', 
 'La historia de Elizabeth Bennet y el señor Darcy, entre malentendidos y amores.'),
('Harry Potter y la Piedra Filosofal', 'J.K. Rowling', 'Fantasía', 20, 22.00,
 'Primer libro de la saga Harry Potter', 
 'Harry descubre que es un mago y asiste a Hogwarts, donde comienza su aventura mágica.');

-- -----------------------------
-- Insertar datos en pedidos
-- -----------------------------
INSERT INTO pedidos (id_usuario, id_producto, cantidad, fecha_pedido)
VALUES
(1, 1, 1, '2025-09-11'),  -- Juan pide "Cien Años de Soledad"
(2, 2, 2, '2025-09-11');  -- María pide "El Principito"
