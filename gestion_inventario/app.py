from flask import Flask, render_template, request, redirect, url_for, flash
from models import Producto, ProductoRepository, Inventario


# Configuración de la aplicación

app = Flask(__name__)
app.secret_key = "supersecreto"  # Clave para sesiones y mensajes flash (cambiar en producción)


# Inicialización del inventario

repo = ProductoRepository("inventario.sqlite3")  # Repositorio SQLite
inventario = Inventario(repo)                     # Carga los productos en memoria


# Ruta principal: listar todos los libros

@app.route("/")
def index():
    productos = inventario.listar_todos()             # Obtener todos los libros
    return render_template("index.html", productos=productos)  # Renderizar plantilla


# Ruta de búsqueda por título

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()        # Obtener la cadena de búsqueda
    if query:
        productos = inventario.buscar_por_nombre(query)  # Buscar libros por título
    else:
        productos = inventario.listar_todos()       # Si no hay búsqueda, mostrar todos
    return render_template("index.html", productos=productos)


# Ruta para agregar un nuevo libro

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            id_ = int(request.form["id"])
            nombre = request.form["nombre"]
            cantidad = int(request.form["cantidad"])
            precio = float(request.form["precio"])

            # Crear instancia de Producto y agregar al inventario
            producto = Producto(id_, nombre, cantidad, precio)
            inventario.agregar_producto(producto)

            flash("Producto agregado correctamente ✅", "success")  # Mensaje de éxito
            return redirect(url_for("index"))  # Redirigir a la página principal

        except Exception as e:
            flash(str(e), "danger")  # Mostrar errores si algo falla

    return render_template("add.html")  # Mostrar formulario si es GET


# Ruta para actualizar un libro existente

@app.route("/update/<int:id_>", methods=["GET", "POST"])
def update(id_):
    producto = repo.obtener(id_)                  # Obtener producto por ID
    if not producto:
        flash("Producto no encontrado ⚠️", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            # Actualizar datos con valores del formulario
            nombre = request.form["nombre"]
            cantidad = int(request.form["cantidad"])
            precio = float(request.form["precio"])

            producto.set_nombre(nombre)
            producto.set_cantidad(cantidad)
            producto.set_precio(precio)

            inventario.actualizar_producto(producto)          # Guardar cambios
            flash("Producto actualizado ✅", "success")
            return redirect(url_for("index"))

        except Exception as e:
            flash(str(e), "danger")  # Mostrar errores

    return render_template("update.html", producto=producto)  # Mostrar formulario con datos actuales


# Ruta para eliminar un libro

@app.route("/delete/<int:id_>")
def delete(id_):
    try:
        inventario.eliminar_producto(id_)              # Eliminar del inventario
        flash("Producto eliminado 🗑️", "success")      # Mensaje de éxito
    except Exception as e:
        flash(str(e), "danger")                         # Mostrar errores

    return redirect(url_for("index"))                  # Volver a la lista de libros


# Ejecutar la aplicación

if __name__ == "__main__":
    app.run(debug=True)  # Ejecutar servidor Flask en modo debug

