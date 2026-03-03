from sqlite3 import connect
from dotenv import load_dotenv
import os

load_dotenv()
DB_PATH = os.getenv("DATABASE", "./data/forum.sqlite3")


def init_db(db_name: str = DB_PATH):

    data_dir = os.path.join(os.getcwd(), "data")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    with connect(db_name) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cargo TEXT NOT NULL)
        """)
        conn.commit()

