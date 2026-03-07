from sqlite3 import connect
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def init_db(db_name: str = DB_PATH):
    data_dir = os.path.dirname(db_name)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    with connect(db_name) as conn:
        # Tabela de Usuários
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cargo TEXT NOT NULL,
            foto TEXT DEFAULT 'default.png'
        )
        """)
        
        # Tabela de Comentários com STATUS
        conn.execute("""
        CREATE TABLE IF NOT EXISTS comentario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tag TEXT NOT NULL,
            destino TEXT NOT NULL,
            status TEXT DEFAULT 'aberto', -- Coluna adicionada aqui
            pai_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (pai_id) REFERENCES comentario(id) ON DELETE CASCADE
        )
        """)
        conn.commit()
    
    # Chama a migração automática para garantir que quem já tem o banco receba a coluna
    migrar_banco_existente(db_name)

def migrar_banco_existente(db_name):
    """Adiciona a coluna status caso ela não exista no arquivo .sqlite3 atual"""
    with connect(db_name) as conn:
        try:
            conn.execute("ALTER TABLE comentario ADD COLUMN status TEXT DEFAULT 'aberto'")
            conn.commit()
            print("Coluna 'status' adicionada com sucesso ao banco existente.")
        except:
            # Se der erro, é porque a coluna já existe, então não fazemos nada
            pass

def conectar():
    from sqlite3 import Row
    conn = connect(DB_PATH)
    conn.row_factory = Row
    return conn