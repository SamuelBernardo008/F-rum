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

# ==========================================
# CRIAÇÃO E BUSCA
# ==========================================

def criar_usuario(nome, email, senha, cargo):
    """Cria um novo usuário já definindo a foto padrão."""
    senha_hash = generate_password_hash(senha)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Adicionamos a coluna 'foto' aqui para novos registros
        cursor.execute(
            "INSERT INTO usuario (nome, email, senha, cargo, foto) VALUES (?, ?, ?, ?, ?)",
            (nome, email, senha_hash, cargo, 'default.png')
        )
        conn.commit()

def buscar_usuario_por_email(email):
    """Busca os dados completos do usuário, incluindo a foto."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ==========================================
# SEGURANÇA E PERFIL
# ==========================================

def verificar_senha(usuario, senha_digitada):
    """Compara a senha digitada com o hash do banco."""
    return check_password_hash(usuario['senha'], senha_digitada)

def atualizar_foto_usuario(usuario_id, nome_arquivo):
    """Atualiza o nome do arquivo de imagem no banco de dados."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuario SET foto = ? WHERE id = ?", 
            (nome_arquivo, usuario_id)
        )
        conn.commit()

def buscar_usuario_por_id(id):
    """Útil para carregar dados no perfil se necessário."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email, cargo, foto FROM usuario WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None