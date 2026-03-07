from models.database import conectar

def alternar_curtida(usuario_id, comentario_id):
    """Se já curtiu, remove. Se não curtiu, adiciona."""
    with conectar() as conn:
        cursor = conn.cursor()
        # Verifica se já existe
        cursor.execute("SELECT id FROM curtida WHERE usuario_id = ? AND comentario_id = ?", 
                       (usuario_id, comentario_id))
        curtida = cursor.fetchone()

        if curtida:
            conn.execute("DELETE FROM curtida WHERE id = ?", (curtida['id'],))
            status = "removido"
        else:
            conn.execute("INSERT INTO curtida (usuario_id, comentario_id) VALUES (?, ?)", 
                         (usuario_id, comentario_id))
            status = "adicionado"
        conn.commit()
        return status

def contar_curtidas(comentario_id):
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM curtida WHERE comentario_id = ?", (comentario_id,))
        return cursor.fetchone()[0]

def usuario_curtiu(usuario_id, comentario_id):
    """Verifica se o usuário logado já curtiu aquele post específico."""
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM curtida WHERE usuario_id = ? AND comentario_id = ?", 
                       (usuario_id, comentario_id))
        return cursor.fetchone() is not None