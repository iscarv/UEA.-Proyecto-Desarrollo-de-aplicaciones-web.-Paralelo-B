import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

DB_PATH = Path("inventario.sqlite3")


# Clase Producto adaptada para Librería

@dataclass
class Producto:
    """
    Representa un libro en el inventario.
    """
    id: int
    titulo: str      # Título del libro
    autor: str       # Autor del libro
    categoria: str   # Categoría (ej: novela, poesía)
    cantidad: int    # Cantidad disponible
    precio: float    # Precio unitario

    def __post_init__(self) -> None:
        """
        Validaciones al crear la instancia.
        """
        self.titulo = self.titulo.strip()
        self.autor = self.autor.strip()
        self.categoria = self.categoria.strip()
        if not self.titulo:
            raise ValueError("El título no puede estar vacío.")
        if not self.autor:
            raise ValueError("El autor no puede estar vacío.")
        if not self.categoria:
            raise ValueError("La categoría no puede estar vacía.")
        if self.cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        if self.precio < 0:
            raise ValueError("El precio no puede ser negativo.")

    # --- Métodos setters ---
    def set_titulo(self, nuevo_titulo: str) -> None:
        """Actualiza el título validando que no esté vacío."""
        nuevo = nuevo_titulo.strip()
        if not nuevo:
            raise ValueError("El título no puede estar vacío.")
        self.titulo = nuevo

    def set_autor(self, nuevo_autor: str) -> None:
        """Actualiza el autor validando que no esté vacío."""
        nuevo = nuevo_autor.strip()
        if not nuevo:
            raise ValueError("El autor no puede estar vacío.")
        self.autor = nuevo

    def set_categoria(self, nueva_categoria: str) -> None:
        """Actualiza la categoría validando que no esté vacía."""
        nuevo = nueva_categoria.strip()
        if not nuevo:
            raise ValueError("La categoría no puede estar vacía.")
        self.categoria = nuevo

    def set_cantidad(self, nueva_cantidad: int) -> None:
        """Actualiza la cantidad validando que no sea negativa."""
        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self.cantidad = nueva_cantidad

    def set_precio(self, nuevo_precio: float) -> None:
        """Actualiza el precio validando que no sea negativo."""
        if nuevo_precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.precio = nuevo_precio

    def to_tuple(self) -> tuple:
        """Convierte el objeto en una tupla para inserción en SQLite."""
        return (self.id, self.titulo, self.autor, self.categoria, self.cantidad, self.precio)



# Repositorio SQLite con campo categoría

class ProductoRepository:
    """
    Gestiona la persistencia de los libros en SQLite.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()  # Crear tabla si no existe

    def _conn(self) -> sqlite3.Connection:
        """Crea y devuelve una conexión a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Crea la tabla 'productos' si no existe."""
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad >= 0),
                    precio REAL NOT NULL CHECK(precio >= 0)
                )
                """
            )

    # --- Métodos CRUD (Create,Read, Update, Delete)---
    def crear(self, p: Producto) -> None:
        """Inserta un nuevo producto en la base de datos."""
        with self._conn() as con:
            con.execute(
                "INSERT INTO productos(id, titulo, autor, categoria, cantidad, precio) VALUES(?,?,?,?,?,?)",
                p.to_tuple(),
            )

    def actualizar(self, p: Producto) -> None:
        """Actualiza un producto existente."""
        with self._conn() as con:
            cur = con.execute(
                "UPDATE productos SET titulo=?, autor=?, categoria=?, cantidad=?, precio=? WHERE id=?",
                (p.titulo, p.autor, p.categoria, p.cantidad, p.precio, p.id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"No existe producto con ID {p.id}")

    def eliminar(self, id_: int) -> None:
        """Elimina un producto por ID."""
        with self._conn() as con:
            cur = con.execute("DELETE FROM productos WHERE id=?", (id_,))
            if cur.rowcount == 0:
                raise KeyError(f"No existe producto con ID {id_}")

    def obtener(self, id_: int) -> Optional[Producto]:
        """Obtiene un producto por ID, devuelve None si no existe."""
        with self._conn() as con:
            row = con.execute("SELECT * FROM productos WHERE id=?", (id_,)).fetchone()
            if not row:
                return None
            return Producto(
                int(row["id"]),
                row["titulo"],
                row["autor"],
                row["categoria"],
                int(row["cantidad"]),
                float(row["precio"]),
            )

    def listar(self) -> List[Producto]:
        """Devuelve todos los productos ordenados por ID."""
        with self._conn() as con:
            rows = con.execute("SELECT * FROM productos ORDER BY id").fetchall()
            return [
                Producto(
                    int(r["id"]),
                    r["titulo"],
                    r["autor"],
                    r["categoria"],
                    int(r["cantidad"]),
                    float(r["precio"]),
                )
                for r in rows
            ]



# Inventario en memoria con índices

class Inventario:
    """
    Mantiene los productos en memoria para operaciones rápidas.
    Indexa los títulos para búsquedas eficientes.
    """

    def __init__(self, repo: ProductoRepository) -> None:
        self.repo = repo
        self._items: Dict[int, Producto] = {}       # Diccionario por ID
        self._index_nombre: Dict[str, Set[int]] = {}  # Índice por título (normalizado)
        self._cargar_desde_bd()

    # --- Métodos internos ---
    def _normaliza(self, titulo: str) -> str:
        """Normaliza el título para búsquedas (minusculas, sin espacios)."""
        return titulo.strip().casefold()

    def _indexar(self, p: Producto) -> None:
        """Agrega el producto al índice por título."""
        clave = self._normaliza(p.titulo)
        self._index_nombre.setdefault(clave, set()).add(p.id)

    def _desindexar(self, p: Producto) -> None:
        """Elimina el producto del índice por título."""
        clave = self._normaliza(p.titulo)
        ids = self._index_nombre.get(clave)
        if ids:
            ids.discard(p.id)
            if not ids:
                self._index_nombre.pop(clave, None)

    def _cargar_desde_bd(self) -> None:
        """Carga todos los productos desde la base de datos al inventario en memoria."""
        for p in self.repo.listar():
            self._items[p.id] = p
            self._indexar(p)

    # --- Métodos CRUD públicos ---
    def agregar_producto(self, p: Producto) -> None:
        """Agrega un nuevo producto al inventario y a la base de datos."""
        if p.id in self._items:
            raise KeyError(f"Ya existe producto con ID {p.id}")
        self.repo.crear(p)
        self._items[p.id] = p
        self._indexar(p)

    def eliminar_producto(self, id_: int) -> None:
        """Elimina un producto por ID del inventario y la base de datos."""
        p = self._items.get(id_)
        if not p:
            raise KeyError(f"No existe producto con ID {id_}")
        self.repo.eliminar(id_)
        self._desindexar(p)
        self._items.pop(id_)

    def actualizar_producto(self, p: Producto) -> None:
        """Actualiza un producto en inventario y base de datos, y reindexa títulos."""
        if p.id not in self._items:
            raise KeyError(f"No existe producto con ID {p.id}")
        self.repo.actualizar(p)
        self._items[p.id] = p
        # Reindexar todo el índice por título
        self._index_nombre = {}
        for prod in self._items.values():
            self._indexar(prod)

    def buscar_por_nombre(self, titulo: str) -> List[Producto]:
        """Busca productos por título (insensible a mayúsculas/minúsculas)."""
        clave = self._normaliza(titulo)
        ids = self._index_nombre.get(clave, set())
        return [self._items[i] for i in ids]

    def listar_todos(self) -> List[Producto]:
        """Devuelve todos los productos ordenados por ID."""
        return [self._items[k] for k in sorted(self._items.keys())]

