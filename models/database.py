from sqlite3 import connect, Row
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")

def init_db(db_name: str = DB_PATH):
    """Cria o banco de dados e as tabelas se não existirem."""
    data_dir = os.path.dirname(db_name)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    with connect(db_name) as conn:
        # 1. TABELA DE USUÁRIOS
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
        
        # 2. TABELA DE COMENTÁRIOS (POSTS)
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

        # 3. TABELA DE NOTIFICAÇÕES (NOVA)
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
        
        conn.commit()
    
    # Roda migrações para bancos que já foram criados anteriormente
    migrar_banco_existente(db_name)

def migrar_banco_existente(db_name):
    """Garante que colunas novas sejam adicionadas a tabelas antigas."""
    with connect(db_name) as conn:
        # Adiciona coluna 'status' caso o usuário já tivesse a tabela 'comentario' sem ela
        try:
            conn.execute("ALTER TABLE comentario ADD COLUMN status TEXT DEFAULT 'aberto'")
            conn.commit()
            print("Coluna 'status' injetada com sucesso.")
        except:
            pass # Coluna já existe

def conectar():
    """Retorna uma conexão configurada para retornar dicionários (Row)."""
    conn = connect(DB_PATH)
    conn.row_factory = Row
    return conn