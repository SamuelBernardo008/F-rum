from sqlite3 import connect, Row
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def get_db_connection():
    conn = connect(DB_PATH)
    # Permite acessar colunas pelo nome: usuario['cargo']
    conn.row_factory = Row 
    return conn

def criar_usuario(nome, email, senha, cargo):
    senha_hash = generate_password_hash(senha)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuario (nome, email, senha, cargo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, cargo)
        )
        conn.commit()

def buscar_usuario_por_email(email):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def verificar_senha(usuario, senha_digitada):
    # Agora usamos a chave 'senha' do dicionário
    return check_password_hash(usuario['senha'], senha_digitada)