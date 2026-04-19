from sqlite3 import connect, Row
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def get_db_connection():
    conn = connect(DB_PATH)
    conn.row_factory = Row 
    return conn


def criar_usuario(nome, email, senha, cargo):
    """Cria um novo usuário já definindo a foto padrão."""
    senha_hash = generate_password_hash(senha)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO usuario (nome, email, senha, cargo, foto) VALUES (?, ?, ?, ?, ?)",
            (nome, email, senha_hash, cargo, 'default.png')
        )
        conn.commit()

def buscar_usuario_por_email(email):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def verificar_senha(usuario, senha_digitada):
    return check_password_hash(usuario['senha'], senha_digitada)

def atualizar_foto_usuario(usuario_id, nome_arquivo):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuario SET foto = ? WHERE id = ?", 
            (nome_arquivo, usuario_id)
        )
        conn.commit()

def buscar_usuario_por_id(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email, cargo, foto FROM usuario WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None