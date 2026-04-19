from sqlite3 import connect, Row
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def init_db(db_name: str = DB_PATH):
    data_dir = os.path.dirname(db_name)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    with connect(db_name) as conn:
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
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS comentario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tag TEXT NOT NULL,
            destino TEXT NOT NULL,
            status TEXT DEFAULT 'aberto',
            pai_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (pai_id) REFERENCES comentario(id) ON DELETE CASCADE
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS notificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,      -- Quem vai receber o aviso
            mensagem TEXT NOT NULL,           -- O texto da notificação
            lida INTEGER DEFAULT 0,           -- 0 = Não lida, 1 = Lida
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            link TEXT,                        -- URL para onde redirecionar ao clicar
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS curtida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            comentario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
            FOREIGN KEY (comentario_id) REFERENCES comentario(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, comentario_id) -- Impede curtir duas vezes o mesmo post
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,         -- 'Bug' ou 'Sugestão'
            texto TEXT NOT NULL,
            status TEXT DEFAULT 'aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
    
    migrar_banco_existente(db_name)

def migrar_banco_existente(db_name):
    with connect(db_name) as conn:
        try:
            conn.execute("ALTER TABLE comentario ADD COLUMN status TEXT DEFAULT 'aberto'")
            conn.commit()
            print("Coluna 'status' injetada com sucesso.")
        except:
            pass 

def conectar():
    """Retorna uma conexão configurada para retornar dicionários (Row)."""
    conn = connect(DB_PATH)
    conn.row_factory = Row
    return conn