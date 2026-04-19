from sqlite3 import connect, Row
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def get_db_connection():
    conn = connect(DB_PATH)
    conn.row_factory = Row  
    return conn


def criar_comentario(texto, usuario_id, tag, destino, pai_id=None): 
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comentario (texto, usuario_id, tag, destino, pai_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (texto, usuario_id, tag, destino, pai_id, 'aberto')
        )
        conn.commit()


def listar_comentarios():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.id,
                c.texto,
                c.tag,
                c.destino,
                c.status,  -- PUXA O STATUS DO BANCO
                c.data_criacao,
                c.usuario_id,
                c.pai_id,
                u.nome AS autor,
                u.cargo AS cargo_autor,
                u.foto AS foto,
                u_pai.nome AS autor_respondido
            FROM comentario c
            JOIN usuario u ON c.usuario_id = u.id
            LEFT JOIN comentario c_pai ON c.pai_id = c_pai.id
            LEFT JOIN usuario u_pai ON c_pai.usuario_id = u_pai.id
            ORDER BY c.data_criacao DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def atualizar_status_comentario(id_comentario, novo_status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE comentario 
            SET status = ? 
            WHERE id = ?
        """, (novo_status, id_comentario))
        conn.commit()


def buscar_comentario_por_id(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comentario WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def listar_comentarios_por_usuario(usuario_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                comentario.*, 
                usuario.foto 
            FROM comentario 
            JOIN usuario ON comentario.usuario_id = usuario.id
            WHERE usuario_id = ?
            ORDER BY data_criacao DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def atualizar_comentario(id_comentario, novo_texto, nova_tag):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE comentario 
            SET texto = ?, tag = ? 
            WHERE id = ?
        """, (novo_texto, nova_tag, id_comentario))
        conn.commit()


def excluir_comentario(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM comentario WHERE id = ?", (id,))
        conn.commit()