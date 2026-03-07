from models.database import conectar

def criar_notificacao(usuario_id, mensagem, link=None):
    """Cria uma nova notificação para um usuário específico."""
    with conectar() as conn:
        conn.execute("""
            INSERT INTO notificacao (usuario_id, mensagem, link)
            VALUES (?, ?, ?)
        """, (usuario_id, mensagem, link))
        conn.commit()

def listar_notificacoes_usuario(usuario_id, apenas_nao_lidas=False):
    """Retorna as notificações do usuário, das mais recentes para as antigas."""
    sql = "SELECT * FROM notificacao WHERE usuario_id = ?"
    if apenas_nao_lidas:
        sql += " AND lida = 0"
    
    sql += " ORDER BY data_criacao DESC LIMIT 10"
    
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (usuario_id,))
        return [dict(row) for row in cursor.fetchall()]

def contar_notificacoes_pendentes(usuario_id):
    """Retorna o número de notificações não lidas (para o contador do sininho)."""
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notificacao WHERE usuario_id = ? AND lida = 0", (usuario_id,))
        return cursor.fetchone()[0]

def marcar_todas_como_lidas(usuario_id):
    """Marca todas as notificações de um usuário como lidas."""
    with conectar() as conn:
        conn.execute("UPDATE notificacao SET lida = 1 WHERE usuario_id = ?", (usuario_id,))
        conn.commit()

def marcar_uma_como_lida(notificacao_id):
    """Marca uma notificação específica como lida."""
    with conectar() as conn:
        conn.execute("UPDATE notificacao SET lida = 1 WHERE id = ?", (notificacao_id,))
        conn.commit()

def deletar_notificacoes_antigas(usuario_id, limite=20):
    """Limpa o banco deletando notificações antigas para não sobrecarregar."""
    with conectar() as conn:
        conn.execute("""
            DELETE FROM notificacao WHERE usuario_id = ? AND id NOT IN (
                SELECT id FROM notificacao WHERE usuario_id = ? 
                ORDER BY data_criacao DESC LIMIT ?
            )
        """, (usuario_id, usuario_id, limite))
        conn.commit()