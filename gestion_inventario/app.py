from flask import Flask, render_template, request, redirect, url_for, flash
from models import Producto, ProductoRepository, Inventario


# -----------------------------
# Configuración de la aplicación
# -----------------------------
app = Flask(__name__)
app.secret_key = "supersecreto"  # Clave para sesiones y mensajes flash (cambiar en producción)


# -----------------------------
# Inicialización del inventario
# -----------------------------
repo = ProductoRepository("inventario.sqlite3")  # Repositorio SQLite
inventario = Inventario(repo)                     # Carga los productos en memoria


# -----------------------------
# Ruta principal (Home)
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# Ruta "Acerca de"
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# -----------------------------
# Ruta Inventario (lista de libros)
# -----------------------------
@app.route("/inventario")
def inventario_view():
    productos = inventario.listar_todos()
    return render_template("index.html", productos=productos)


# -----------------------------
# Ruta de búsqueda por título
# -----------------------------
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if query:
        productos = inventario.buscar_por_nombre(query)
    else:
        productos = inventario.listar_todos()
    return render_template("index.html", productos=productos)


# -----------------------------
# Ruta para agregar un nuevo libro
# -----------------------------
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        try:
            id_ = int(request.form["id"])
            titulo = request.form["titulo"]
            autor = request.form["autor"]
            categoria = request.form["categoria"]
            cantidad = int(request.form["cantidad"])
            precio = float(request.form["precio"])

            producto = Producto(id_, titulo, autor, categoria, cantidad, precio)
            inventario.agregar_producto(producto)

            flash("Libro agregado correctamente ✅", "success")
            return redirect(url_for("inventario_view"))

        except Exception as e:
            flash(str(e), "danger")

    return render_template("add.html")


# -----------------------------
# Ruta para actualizar un libro existente
# -----------------------------
@app.route("/update/<int:id_>", methods=["GET", "POST"])
def update(id_):
    producto = repo.obtener(id_)
    if not producto:
        flash("Libro no encontrado ⚠️", "warning")
        return redirect(url_for("inventario_view"))

    if request.method == "POST":
        try:
            titulo = request.form["titulo"]
            autor = request.form["autor"]
            categoria = request.form["categoria"]
            cantidad = int(request.form["cantidad"])
            precio = float(request.form["precio"])

            producto.set_titulo(titulo)
            producto.set_autor(autor)
            producto.set_categoria(categoria)
            producto.set_cantidad(cantidad)
            producto.set_precio(precio)

            inventario.actualizar_producto(producto)
            flash("Libro actualizado ✅", "success")
            return redirect(url_for("inventario_view"))

        except Exception as e:
            flash(str(e), "danger")

    return render_template("update.html", producto=producto)


# -----------------------------
# Ruta para eliminar un libro
# -----------------------------
@app.route("/delete/<int:id_>")
def delete(id_):
    try:
        inventario.eliminar_producto(id_)
        flash("Libro eliminado 🗑️", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("inventario_view"))


# -----------------------------
# Ejecutar la aplicación
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
