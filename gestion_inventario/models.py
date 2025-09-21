import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# Flask-Login
from flask_login import UserMixin


# Configuración SQLite

DB_PATH = Path("inventario.sqlite3")



# Modelo de Usuario (MySQL / Flask-Login)

class Usuario(UserMixin):
    """ Modelo de Usuario compatible con Flask-Login."""
  
    def __init__(self, id_usuario: int, nombre: str, email: str, password_hash: str):
        self.id = id_usuario   # Flask-Login espera "id"
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash

    def __repr__(self) -> str:
        return f"<Usuario {self.id} - {self.nombre}>"



# Modelo de Producto (SQLite)

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
        """Validaciones al crear la instancia."""
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

    def to_tuple(self) -> tuple:
        return (self.id, self.titulo, self.autor, self.categoria, self.cantidad, self.precio)



# Repositorio de Productos (SQLite)

class ProductoRepository:
    """
    Gestiona la persistencia de los libros en SQLite.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
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

    # --- Métodos CRUD ---
    def crear(self, p: Producto) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT INTO productos(id, titulo, autor, categoria, cantidad, precio) VALUES(?,?,?,?,?,?)",
                p.to_tuple(),
            )

    def actualizar(self, p: Producto) -> None:
        with self._conn() as con:
            cur = con.execute(
                "UPDATE productos SET titulo=?, autor=?, categoria=?, cantidad=?, precio=? WHERE id=?",
                (p.titulo, p.autor, p.categoria, p.cantidad, p.precio, p.id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"No existe producto con ID {p.id}")

    def eliminar(self, id_: int) -> None:
        with self._conn() as con:
            cur = con.execute("DELETE FROM productos WHERE id=?", (id_,))
            if cur.rowcount == 0:
                raise KeyError(f"No existe producto con ID {id_}")

    def obtener(self, id_: int) -> Optional[Producto]:
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

    def buscar_por_nombre(self, titulo: str) -> List[Producto]:
        """Búsqueda parcial por título usando LIKE"""
        with self._conn() as con:
            rows = con.execute(
                "SELECT * FROM productos WHERE titulo LIKE ? ORDER BY id",
                (f"%{titulo}%",),
            ).fetchall()
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



# Inventario en memoria

class Inventario:
    """
    Mantiene los productos en memoria para operaciones rápidas.
    """

    def __init__(self, repo: ProductoRepository) -> None:
        self.repo = repo
        self._items: Dict[int, Producto] = {}
        self._cargar_desde_bd()

    def _cargar_desde_bd(self) -> None:
        for p in self.repo.listar():
            self._items[p.id] = p

    # CRUD
    def agregar_producto(self, p: Producto) -> None:
        if p.id in self._items:
            raise KeyError(f"Ya existe producto con ID {p.id}")
        self.repo.crear(p)
        self._items[p.id] = p

    def eliminar_producto(self, id_: int) -> None:
        if id_ not in self._items:
            raise KeyError(f"No existe producto con ID {id_}")
        self.repo.eliminar(id_)
        self._items.pop(id_)

    def actualizar_producto(self, p: Producto) -> None:
        if p.id not in self._items:
            raise KeyError(f"No existe producto con ID {p.id}")
        self.repo.actualizar(p)
        self._items[p.id] = p

    def buscar_por_nombre(self, titulo: str) -> List[Producto]:
        """Delegamos búsqueda parcial al repositorio"""
        return self.repo.buscar_por_nombre(titulo)

    def listar_todos(self) -> List[Producto]:
        return [self._items[k] for k in sorted(self._items.keys())]
