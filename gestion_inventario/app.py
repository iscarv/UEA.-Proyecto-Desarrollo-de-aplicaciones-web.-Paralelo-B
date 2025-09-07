from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, json, csv
from pathlib import Path


# Configuración de la aplicación

app = Flask(__name__)
app.secret_key = "supersecreto"


# Directorios y archivos

DATA_DIR = Path("datos")
DB_DIR = Path("database")
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

TXT_FILE = DATA_DIR / "datos.txt"
JSON_FILE = DATA_DIR / "datos.json"
CSV_FILE = DATA_DIR / "datos.csv"
USUARIOS_DB = DB_DIR / "usuarios.db"
INVENTARIO_DB = DB_DIR / "inventario.sqlite3"  # base de inventario


# Función de conexión SQLite

def get_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


# Inicializar tabla usuarios

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


# Rutas Home y About

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")


# Inventario

@app.route("/inventario")
def inventario_view():
    conn = get_db_connection(INVENTARIO_DB)
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template("index.html", productos=productos)

# Añadir producto
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        id_ = request.form.get("id")
        titulo = request.form.get("titulo")
        autor = request.form.get("autor")
        categoria = request.form.get("categoria")
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")

        conn = get_db_connection(INVENTARIO_DB)
        conn.execute(
            "INSERT INTO productos (id, titulo, autor, categoria, cantidad, precio) VALUES (?, ?, ?, ?, ?, ?)",
            (id_, titulo, autor, categoria, cantidad, precio)
        )
        conn.commit()
        conn.close()
        flash("Producto agregado correctamente ✅", "success")
        return redirect(url_for("inventario_view"))

    # Producto=None indica que es un formulario para crear
    return render_template("add.html", producto=None)

# Editar producto
@app.route("/update/<int:id_>", methods=["GET", "POST"])
def update(id_):
    conn = get_db_connection(INVENTARIO_DB)
    producto = conn.execute("SELECT * FROM productos WHERE id=?", (id_,)).fetchone()

    if request.method == "POST":
        titulo = request.form.get("titulo")
        autor = request.form.get("autor")
        categoria = request.form.get("categoria")
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")

        conn.execute(
            "UPDATE productos SET titulo=?, autor=?, categoria=?, cantidad=?, precio=? WHERE id=?",
            (titulo, autor, categoria, cantidad, precio, id_)
        )
        conn.commit()
        conn.close()
        flash("Producto actualizado ✅", "success")
        return redirect(url_for("inventario_view"))

    conn.close()
    # Pasamos el producto existente para precargar los campos
    return render_template("add.html", producto=producto)

# Eliminar producto
@app.route("/delete/<int:id_>")
def delete(id_):
    conn = get_db_connection(INVENTARIO_DB)
    conn.execute("DELETE FROM productos WHERE id=?", (id_,))
    conn.commit()
    conn.close()
    flash("Producto eliminado ✅", "success")
    return redirect(url_for("inventario_view"))

# Buscar producto
@app.route("/search")
def search():
    query = request.args.get("q", "")
    conn = get_db_connection(INVENTARIO_DB)
    productos = conn.execute(
        "SELECT * FROM productos WHERE titulo LIKE ?", ('%' + query + '%',)
    ).fetchall()
    conn.close()
    return render_template("index.html", productos=productos)


# Usuarios (persistencia múltiple)

@app.route("/usuarios")
def usuarios_view():
    conn = get_db_connection(USUARIOS_DB)
    rows = conn.execute("SELECT * FROM usuarios").fetchall()
    conn.close()

    datos = [dict(row) for row in rows]

    return render_template("resultado.html", datos=datos, tipo="SQLite")

@app.route("/formulario")
def formulario():
    return render_template("formulario.html")

@app.route("/guardar_txt", methods=["POST"])
def guardar_txt():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    with open(TXT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{nombre},{correo}\n")
    flash("Datos guardados en TXT ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/leer_txt")
def leer_txt():
    datos = []
    if TXT_FILE.exists():
        with open(TXT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                partes = line.strip().split(",")
                if len(partes) == 2:
                    nombre, correo = partes
                    datos.append({"nombre": nombre, "correo": correo})
    if not datos:
        flash("No hay usuarios guardados en TXT ⚠️", "warning")
    return render_template("resultado.html", datos=datos, tipo="TXT")

@app.route("/guardar_json", methods=["POST"])
def guardar_json():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    data = []
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append({"nombre": nombre, "correo": correo})
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    flash("Datos guardados en JSON ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/leer_json")
def leer_json():
    datos = []
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
    return render_template("resultado.html", datos=datos, tipo="JSON")

@app.route("/guardar_csv", methods=["POST"])
def guardar_csv():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nombre", "correo"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"nombre": nombre, "correo": correo})
    flash("Datos guardados en CSV ✅", "success")
    return redirect(url_for("formulario"))

@app.route("/leer_csv")
def leer_csv():
    datos = []
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                datos.append(row)
    return render_template("resultado.html", datos=datos, tipo="CSV")

@app.route("/guardar_sqlite", methods=["POST"])
def guardar_sqlite_usuario():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    conn = get_db_connection(USUARIOS_DB)
    conn.execute("INSERT INTO usuarios (nombre, correo) VALUES (?, ?)", (nombre, correo))
    conn.commit()
    conn.close()
    flash("Datos guardados en SQLite ✅", "success")
    return redirect(url_for("formulario"))


# Ejecutar la aplicación

if __name__ == "__main__":
    app.run(debug=True)


