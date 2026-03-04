from sqlite3 import connect, Row
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

# =========================
# CONEXÃO COM O BANCO
# =========================
def get_db_connection():
    conn = connect(DB_PATH)
    conn.row_factory = Row  # permite acessar por nome
    return conn


# =========================
# CRIAR COMENTÁRIO
# =========================
def criar_comentario(texto, usuario_id, tag, destino): # Adicionado destino
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comentario (texto, usuario_id, tag, destino)
            VALUES (?, ?, ?, ?)
            """,
            (texto, usuario_id, tag, destino)
        )
        conn.commit()

def listar_comentarios():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                comentario.id,
                comentario.texto,
                comentario.tag,
                comentario.destino,  -- Adicionado
                comentario.data_criacao,
                usuario.nome AS autor,
                usuario.cargo AS cargo_autor
            FROM comentario
            JOIN usuario ON comentario.usuario_id = usuario.id
            ORDER BY comentario.data_criacao DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# =========================
# LISTAR COMENTÁRIOS POR TAG
# =========================
def listar_comentarios_por_tag(tag):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                comentario.id,
                comentario.texto,
                comentario.tag,
                comentario.data_criacao,
                usuario.nome AS autor
            FROM comentario
            JOIN usuario ON comentario.usuario_id = usuario.id
            WHERE comentario.tag = ?
            ORDER BY comentario.data_criacao DESC
        """, (tag,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# =========================
# LISTAR COMENTÁRIOS DE UM USUÁRIO
# =========================
def listar_comentarios_por_usuario(usuario_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM comentario
            WHERE usuario_id = ?
            ORDER BY data_criacao DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]