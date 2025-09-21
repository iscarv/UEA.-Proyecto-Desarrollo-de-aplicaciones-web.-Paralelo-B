import mysql.connector
import sqlite3, json, csv
from pathlib import Path
import secrets

from flask import Flask, render_template, request, redirect, url_for, flash, session
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
# Directorios y archivos
# -----------------------------
DATA_DIR = Path("datos")
DB_DIR = Path("database")
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

TXT_FILE = DATA_DIR / "datos.txt"
JSON_FILE = DATA_DIR / "datos.json"
CSV_FILE = DATA_DIR / "datos.csv"
USUARIOS_DB = DB_DIR / "usuarios.db"
INVENTARIO_DB = DB_DIR / "inventario.sqlite3"

# -----------------------------
# Conexión SQLite
# -----------------------------
def get_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar tabla usuarios en SQLite
def init_usuarios_db():
    conn = get_db_connection(USUARIOS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
init_usuarios_db()

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
# Registro
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
# Inventario SQLite
# -----------------------------
@app.route("/inventario")
@login_required
def inventario_view():
    conn = get_db_connection(INVENTARIO_DB)
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template("index.html", productos=productos)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        id_ = request.form.get("id")
        titulo = request.form.get("titulo")
        autor = request.form.get("autor")
        categoria = request.form.get("categoria")
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")

        conn = get_db_connection(INVENTARIO_DB)
        conn.execute("INSERT INTO productos (id, titulo, autor, categoria, cantidad, precio) VALUES (?, ?, ?, ?, ?, ?)",
                     (id_, titulo, autor, categoria, cantidad, precio))
        conn.commit()
        conn.close()
        flash("Producto agregado correctamente ✅", "success")
        return redirect(url_for("inventario_view"))
    return render_template("add.html", producto=None)

@app.route("/update/<int:id_>", methods=["GET", "POST"])
@login_required
def update(id_):
    conn = get_db_connection(INVENTARIO_DB)
    producto = conn.execute("SELECT * FROM productos WHERE id=?", (id_,)).fetchone()

    if request.method == "POST":
        titulo = request.form.get("titulo")
        autor = request.form.get("autor")
        categoria = request.form.get("categoria")
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")
        conn.execute("UPDATE productos SET titulo=?, autor=?, categoria=?, cantidad=?, precio=? WHERE id=?",
                     (titulo, autor, categoria, cantidad, precio, id_))
        conn.commit()
        conn.close()
        flash("Producto actualizado ✅", "success")
        return redirect(url_for("inventario_view"))

    conn.close()
    return render_template("add.html", producto=producto)

@app.route("/delete/<int:id_>")
@login_required
def delete(id_):
    conn = get_db_connection(INVENTARIO_DB)
    conn.execute("DELETE FROM productos WHERE id=?", (id_,))
    conn.commit()
    conn.close()
    flash("Producto eliminado ✅", "success")
    return redirect(url_for("inventario_view"))

@app.route("/search")
@login_required
def search():
    query = request.args.get("q", "")
    conn = get_db_connection(INVENTARIO_DB)
    productos = conn.execute("SELECT * FROM productos WHERE titulo LIKE ?", ('%' + query + '%',)).fetchall()
    conn.close()
    return render_template("index.html", productos=productos)

# -----------------------------
# Usuarios SQLite/TXT/JSON/CSV
# -----------------------------
@app.route("/formulario", methods=["GET", "POST"])
@login_required
def formulario():
    return render_template("formulario.html")

@app.route("/guardar_sqlite_usuario", methods=["POST"])
@login_required
def guardar_sqlite_usuario():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    conn = get_db_connection(USUARIOS_DB)
    conn.execute("INSERT INTO usuarios (nombre, correo) VALUES (?, ?)", (nombre, correo))
    conn.commit()
    conn.close()
    flash("Usuario guardado en SQLite ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/guardar_txt", methods=["POST"])
@login_required
def guardar_txt():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    with open(TXT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{nombre},{correo}\n")
    flash("Usuario guardado en TXT ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/guardar_json", methods=["POST"])
@login_required
def guardar_json():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    data = []
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append({"nombre": nombre, "correo": correo})
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    flash("Usuario guardado en JSON ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/guardar_csv", methods=["POST"])
@login_required
def guardar_csv():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["nombre", "correo"])
        writer.writerow([nombre, correo])
    flash("Usuario guardado en CSV ✅", "success")
    return redirect(url_for("formulario"))

# -----------------------------
# Leer usuarios
# -----------------------------
@app.route("/leer_txt")
@login_required
def leer_txt():
    usuarios = []
    if TXT_FILE.exists():
        with open(TXT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    nombre, correo = line.strip().split(",", 1)
                    usuarios.append({"nombre": nombre, "correo": correo})
    return render_template("leer_txt.html", usuarios=usuarios)

@app.route("/leer_json")
@login_required
def leer_json():
    usuarios = []
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            usuarios = json.load(f)
    return render_template("leer_json.html", usuarios=usuarios)

@app.route("/leer_csv")
@login_required
def leer_csv():
    usuarios = []
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                usuarios.append({"nombre": row["nombre"], "correo": row["correo"]})
    return render_template("leer_csv.html", usuarios=usuarios)

@app.route("/usuarios")
@login_required
def usuarios_view():
    conn = get_db_connection(USUARIOS_DB)
    usuarios = conn.execute("SELECT * FROM usuarios").fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)

# -----------------------------
# MySQL tablas
# -----------------------------
@app.route("/mysql_tables")
@login_required
def mysql_tables():
    conn = get_mysql_connection_local()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template("mysql_tables.html", tables=tables)

@app.route("/mysql_tables/<table_name>")
@login_required
def ver_tabla(table_name):
    conn = get_mysql_connection_local()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("mysql_data.html", titulo=table_name, datos=rows)

# -----------------------------
# Ejecutar aplicación
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)














