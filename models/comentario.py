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
def criar_comentario(texto, usuario_id, tag, destino, pai_id=None): 
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comentario (texto, usuario_id, tag, destino, pai_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (texto, usuario_id, tag, destino, pai_id)
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
                c.data_criacao,
                c.usuario_id,
                c.pai_id,
                u.nome AS autor,
                u.cargo AS cargo_autor,
                u.foto AS foto,
                u_pai.nome AS autor_respondido  -- Nome de quem está sendo respondido
            FROM comentario c
            JOIN usuario u ON c.usuario_id = u.id
            LEFT JOIN comentario c_pai ON c.pai_id = c_pai.id
            LEFT JOIN usuario u_pai ON c_pai.usuario_id = u_pai.id
            ORDER BY c.data_criacao DESC
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
                usuario.nome AS autor,
                usuario.foto AS foto  -- ADICIONADO: Puxa a foto do autor
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
    
# =========================
# BUSCAR COMENTÁRIO POR ID
# =========================
def buscar_comentario_por_id(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comentario WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# =========================
# ATUALIZAR COMENTÁRIO
# =========================
def atualizar_comentario(id_comentario, novo_texto, nova_tag):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE comentario 
            SET texto = ?, tag = ? 
            WHERE id = ?
        """, (novo_texto, nova_tag, id_comentario))
        conn.commit()

# =========================
# EXCLUIR COMENTÁRIO
# =========================
def excluir_comentario(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM comentario WHERE id = ?", (id,))
        conn.commit()