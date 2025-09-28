import mysql.connector
import json, csv, os, secrets
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------
# Configuración de la aplicación
# -----------------------------
app = Flask(__name__)
app.secret_key = "supersecreto"

# -----------------------------
# Configuración LoginManager
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -----------------------------
# Configuración MySQL
# -----------------------------
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',
    'database': 'desarrollo_web',
    'port': 3308
}

def get_mysql_connection_local():
    return mysql.connector.connect(**MYSQL_CONFIG)

# -----------------------------
# Configuración de subida de archivos
# -----------------------------
UPLOAD_FOLDER = Path("static/portadas")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------
# Modelo Usuario
# -----------------------------
class Usuario(UserMixin):
    def __init__(self, id_usuario, nombre, email, password):
        self.id = id_usuario
        self.nombre = nombre
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_mysql_connection_local()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return Usuario(user_data["id_usuario"], user_data["nombre"], user_data["email"], user_data.get("password"))
    return None

# -----------------------------
# Rutas públicas
# -----------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/about")
def about():
    return render_template("about.html")

# -----------------------------
# Registro de usuarios
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        captcha_input = request.form.get("captcha_input", "").strip()
        stored_captcha = session.get("captcha_code")
        session.pop("captcha_code", None)

        if not stored_captcha or captcha_input != stored_captcha:
            flash("Código de verificación incorrecto ❌", "danger")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Las contraseñas no coinciden ❌", "danger")
            return redirect(url_for("register"))

        conn = get_mysql_connection_local()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("El correo ya está registrado ❌", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                       (nombre, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Registro exitoso ✅, ahora inicia sesión", "success")
        return redirect(url_for("login"))

    captcha_code = str(secrets.randbelow(900000) + 100000)
    session["captcha_code"] = captcha_code
    return render_template("register.html", captcha=captcha_code)

# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        captcha_input = request.form.get("captcha_input", "").strip()
        stored_captcha = session.get("captcha_code")
        session.pop("captcha_code", None)

        if not stored_captcha or captcha_input != stored_captcha:
            flash("Código de verificación incorrecto ❌", "danger")
            return redirect(url_for("login"))

        conn = get_mysql_connection_local()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT id_usuario, nombre, email, password FROM usuarios WHERE email=%s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data and check_password_hash(user_data["password"], password):
            user = Usuario(user_data["id_usuario"], user_data["nombre"], user_data["email"], user_data["password"])
            login_user(user)
            flash(f"Bienvenido, {user.nombre} 🎉", "success")
            return redirect(url_for("home"))
        flash("Correo o contraseña incorrectos ❌", "danger")
        return redirect(url_for("login"))

    captcha_code = str(secrets.randbelow(900000) + 100000)
    session["captcha_code"] = captcha_code
    return render_template("login.html", captcha=captcha_code)

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada 👋", "info")
    return redirect(url_for("login"))

# -----------------------------
# Home
# -----------------------------
@app.route("/home")
@login_required
def home():
    return render_template("home.html", user=current_user)

# -----------------------------
# Usuarios
# -----------------------------
@app.route("/usuarios_view")
@login_required
def usuarios_view():
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario, nombre, email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("usuarios_view.html", usuarios=usuarios)

@app.route("/formulario", methods=["GET", "POST"])
@login_required
def formulario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_mysql_connection_local()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("El correo ya está registrado ❌", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("formulario"))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                       (nombre, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Usuario registrado manualmente ✅", "success")
        return redirect(url_for("usuarios_view"))
    return render_template("formulario.html")

# -----------------------------
# Inventario / Productos
# -----------------------------
@app.route("/inventario", methods=["GET"])
@login_required
def inventario_view():
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    busqueda = request.args.get("busqueda", "").strip()
    if busqueda:
        query = "SELECT * FROM productos WHERE titulo LIKE %s OR autor LIKE %s OR categoria LIKE %s"
        valores = (f"{busqueda}%", f"{busqueda}%", f"{busqueda}%")
    else:
        query = "SELECT * FROM productos"
        valores = ()
    cursor.execute(query, valores)
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("productos.html", productos=productos)

@app.route("/crear", methods=["GET", "POST"])
@login_required
def crear_producto():
    if request.method == "POST":
        titulo = request.form["titulo"]
        autor = request.form["autor"]
        categoria = request.form["categoria"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]
        portada_file = request.files.get("portada")
        portada_filename = None
        if portada_file and allowed_file(portada_file.filename):
            portada_filename = secure_filename(portada_file.filename)
            portada_path = app.config['UPLOAD_FOLDER'] / portada_filename
            portada_file.save(portada_path)

        conexion = get_mysql_connection_local()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO productos (titulo, autor, categoria, cantidad, precio, portada) VALUES (%s, %s, %s, %s, %s, %s)",
            (titulo, autor, categoria, cantidad, precio, portada_filename)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Producto agregado con éxito ✅")
        return redirect(url_for("inventario_view"))
    return render_template("crear.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()
    if request.method == "POST":
        titulo = request.form["titulo"]
        autor = request.form["autor"]
        categoria = request.form["categoria"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]
        portada_file = request.files.get("portada")
        portada_filename = producto["portada"]
        if portada_file and allowed_file(portada_file.filename):
            portada_filename = secure_filename(portada_file.filename)
            portada_path = app.config['UPLOAD_FOLDER'] / portada_filename
            portada_file.save(portada_path)
        cursor.execute(
            "UPDATE productos SET titulo=%s, autor=%s, categoria=%s, cantidad=%s, precio=%s, portada=%s WHERE id_producto=%s",
            (titulo, autor, categoria, cantidad, precio, portada_filename, id)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Producto actualizado ✍️")
        return redirect(url_for("inventario_view"))
    cursor.close()
    conexion.close()
    return render_template("editar.html", producto=producto)

@app.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_producto(id):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    flash("Producto eliminado ❌")
    return redirect(url_for("inventario_view"))

# -----------------------------
# Exportar Usuarios
# -----------------------------
@app.route("/usuarios/<formato>")
@login_required
def usuarios_export(formato):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario AS id, nombre, email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("usuarios_exportados.html", usuarios=usuarios, formato=formato)

@app.route("/usuarios/<formato>/descargar")
@login_required
def descargar_usuarios(formato):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, nombre, email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()

    if formato == "txt":
        contenido = "\n".join([f"{u[0]} - {u[1]} - {u[2]}" for u in usuarios])
        mimetype = "text/plain"
        filename = "usuarios.txt"
    elif formato == "json":
        contenido = json.dumps([{"id": u[0], "nombre": u[1], "email": u[2]} for u in usuarios], indent=4)
        mimetype = "application/json"
        filename = "usuarios.json"
    elif formato == "csv":
        from io import StringIO
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["ID", "Nombre", "Email"])
        writer.writerows(usuarios)
        contenido = si.getvalue()
        mimetype = "text/csv"
        filename = "usuarios.csv"
    else:
        flash("Formato no soportado ❌", "danger")
        return redirect(url_for("usuarios_view"))

    return Response(
        contenido,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# -----------------------------
# CRUD Pedidos
# -----------------------------
@app.route("/pedidos", methods=["GET"])
@login_required
def pedidos_view():
    busqueda = request.args.get("busqueda", "").strip()
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)

    query_base = """
        SELECT p.id_pedido,
               u.nombre AS cliente,
               pr.titulo AS producto,
               p.cantidad,
               p.fecha_pedido AS fecha
        FROM pedidos p
        JOIN usuarios u ON p.id_usuario = u.id_usuario
        JOIN productos pr ON p.id_producto = pr.id_producto
    """

    if busqueda:
        query_base += " WHERE u.nombre LIKE %s OR pr.titulo LIKE %s"
        valores = (f"{busqueda}%", f"{busqueda}%")
        cursor.execute(query_base, valores)
    else:
        cursor.execute(query_base)

    pedidos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("pedidos.html", pedidos=pedidos)

@app.route("/pedidos/crear", methods=["GET", "POST"])
@login_required
def crear_pedido():
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario, nombre FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT id_producto, titulo FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    if request.method == "POST":
        id_usuario = request.form["id_usuario"]
        id_producto = request.form["id_producto"]
        cantidad = request.form["cantidad"]

        conexion = get_mysql_connection_local()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO pedidos (id_usuario, id_producto, cantidad, fecha_pedido) VALUES (%s, %s, %s, NOW())",
            (id_usuario, id_producto, cantidad)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Pedido agregado con éxito ✅")
        return redirect(url_for("pedidos_view"))

    return render_template("crear_pedido.html", usuarios=usuarios, productos=productos)

@app.route("/pedidos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_pedido(id):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pedidos WHERE id_pedido = %s", (id,))
    pedido = cursor.fetchone()
    cursor.execute("SELECT id_usuario, nombre FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT id_producto, titulo FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    if request.method == "POST":
        id_usuario = request.form["id_usuario"]
        id_producto = request.form["id_producto"]
        cantidad = request.form["cantidad"]

        conexion = get_mysql_connection_local()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE pedidos SET id_usuario=%s, id_producto=%s, cantidad=%s WHERE id_pedido=%s",
            (id_usuario, id_producto, cantidad, id)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Pedido actualizado ✍️")
        return redirect(url_for("pedidos_view"))

    return render_template("editar_pedido.html", pedido=pedido, usuarios=usuarios, productos=productos)

@app.route("/pedidos/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_pedido(id):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id_pedido = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    flash("Pedido eliminado ❌")
    return redirect(url_for("pedidos_view"))

@app.route("/pedidos/<formato>/descargar")
@login_required
def descargar_pedidos(formato):
    conexion = get_mysql_connection_local()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id_pedido,
               u.nombre AS cliente,
               pr.titulo AS producto,
               p.cantidad,
               p.fecha_pedido
        FROM pedidos p
        JOIN usuarios u ON p.id_usuario = u.id_usuario
        JOIN productos pr ON p.id_producto = pr.id_producto
    """)
    pedidos = cursor.fetchall()
    cursor.close()
    conexion.close()

    if formato == "txt":
        contenido = "\n".join([f"{p[0]} - {p[1]} - {p[2]} - {p[3]} - {p[4]}" for p in pedidos])
        mimetype = "text/plain"
        filename = "pedidos.txt"
    elif formato == "json":
        contenido = json.dumps([{"id": p[0], "cliente": p[1], "producto": p[2], "cantidad": p[3], "fecha": str(p[4])} for p in pedidos], indent=4)
        mimetype = "application/json"
        filename = "pedidos.json"
    elif formato == "csv":
        from io import StringIO
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["ID", "Cliente", "Producto", "Cantidad", "Fecha"])
        writer.writerows(pedidos)
        contenido = si.getvalue()
        mimetype = "text/csv"
        filename = "pedidos.csv"
    else:
        flash("Formato no soportado ❌", "danger")
        return redirect(url_for("pedidos_view"))

    return Response(
        contenido,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# -----------------------------
# Ejecutar aplicación
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)































