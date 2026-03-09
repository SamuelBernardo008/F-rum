import os 
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from PIL import Image, ImageOps
from functools import wraps
from models.database import init_db, conectar 
from models.usuario import buscar_usuario_por_email, verificar_senha, atualizar_foto_usuario
from models.curtida import alternar_curtida, contar_curtidas, usuario_curtiu
from models.comentario import (
    criar_comentario, 
    listar_comentarios, 
    excluir_comentario, 
    buscar_comentario_por_id, 
    atualizar_comentario,
    listar_comentarios_por_usuario,
    atualizar_status_comentario 
)
from models.notificacao import criar_notificacao, listar_notificacoes_usuario, marcar_todas_como_lidas

app = Flask(__name__)
app.secret_key = "123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

# =========================
# CONTEXT PROCESSOR (O "SININHO")
# =========================
@app.context_processor
def inject_notifications():
    if "usuario_id" in session:
        usuario_id = session["usuario_id"]
        notificacoes = listar_notificacoes_usuario(usuario_id, apenas_nao_lidas=True)
        return dict(notificacoes_usuario=notificacoes, total_notificacoes=len(notificacoes))
    return dict(notificacoes_usuario=[], total_notificacoes=0)

# =========================
# DECORATORS
# =========================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def cargo_required(cargo_permitido):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            usuario_cargo = session.get("cargo")
            if usuario_cargo == "admin":
                return f(*args, **kwargs)
            if usuario_cargo != cargo_permitido:
                try:
                    return redirect(url_for(f"forum_{usuario_cargo}"))
                except:
                    return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================
# ROTAS DE NOTIFICAÇÃO
# =========================

@app.route("/notificacoes/limpar")
@login_required
def limpar_notificacoes():
    marcar_todas_como_lidas(session["usuario_id"])
    return redirect(request.referrer or url_for("home"))

# =========================
# AUTENTICAÇÃO E HOME
# =========================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        cargo = session.get("cargo")
        endpoint = "servico_admin" if cargo == "admin" else f"forum_{cargo}"
        return redirect(url_for(endpoint))

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        usuario = buscar_usuario_por_email(email)

        if usuario and verificar_senha(usuario, senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["cargo"] = usuario["cargo"]
            session["foto"] = usuario["foto"] if usuario.get("foto") else "default.png"
            
            if usuario["cargo"] == "admin":
                return redirect(url_for("servico_admin"))
            return redirect(url_for(f"forum_{usuario['cargo']}"))

        return render_template("login.html", erro="Email ou senha inválidos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# GESTÃO DE COMENTÁRIOS E STATUS
# =========================

@app.route("/comentario", methods=["POST"])
@login_required
def adicionar_comentario():
    id_comentario = request.form.get("id_comentario")
    texto = request.form.get("texto")
    tag = request.form.get("tag")
    destino = request.form.get("origem")
    pai_id = request.form.get("pai_id") 
    usuario_id = session.get("usuario_id")

    if not pai_id or not str(pai_id).strip():
        pai_id = None

    if texto and tag and destino:
        if id_comentario and id_comentario.strip():
            comentario = buscar_comentario_por_id(id_comentario)
            if comentario and (comentario['usuario_id'] == usuario_id or session.get('cargo') == 'admin'):
                atualizar_comentario(id_comentario, texto, tag)
        else:
            novo_id = criar_comentario(texto, usuario_id, tag, destino, pai_id)
            if pai_id:
                post_pai = buscar_comentario_por_id(pai_id)
                if post_pai and post_pai['usuario_id'] != usuario_id:
                    msg = f"{session['nome']} respondeu ao seu tópico: '{texto[:20]}...'"
                    criar_notificacao(post_pai['usuario_id'], msg, link=url_for('ver_thread', id_pai=pai_id))
    
    if pai_id:
        return redirect(url_for('ver_thread', id_pai=pai_id))
    return redirect(url_for(f"forum_{destino}"))

@app.route("/comentario/status/<int:id>/<novo_status>")
@login_required
@cargo_required("admin")
def mudar_status(id, novo_status):
    permitidos = ['aberto', 'andamento', 'resolvido', 'inviavel', 'discussao']
    if novo_status in permitidos:
        atualizar_status_comentario(id, novo_status)
        post = buscar_comentario_por_id(id)
        if post:
            msg = f"O status do seu post foi alterado para: {novo_status.upper()}"
            destino_link = f"forum_{post['destino']}"
            criar_notificacao(post['usuario_id'], msg, link=url_for(destino_link))
            
    return redirect(request.referrer or url_for("home"))

@app.route("/thread/<int:id_pai>")
@login_required
def ver_thread(id_pai):
    pai = buscar_comentario_por_id(id_pai)
    if not pai:
        return redirect(url_for('home'))
    
    todos = listar_comentarios()
    respostas = [c for c in todos if str(c.get('pai_id')) == str(id_pai)]
    return render_template("thread.html", pai=pai, respostas=respostas)

@app.route("/comentario/deletar/<int:id>")
@login_required
def deletar_comentario(id):
    comentario = buscar_comentario_por_id(id)
    if comentario:
        if comentario['usuario_id'] == session.get("usuario_id") or session.get("cargo") == "admin":
            excluir_comentario(id)
    return redirect(request.referrer or url_for("home"))

@app.route("/curtir/<int:id_comentario>")
@login_required
def curtir(id_comentario):
    usuario_id = session.get("usuario_id")
    alternar_curtida(usuario_id, id_comentario)
    return redirect(request.referrer or url_for("home"))

# =========================
# GESTÃO DE FEEDBACKS (BUGS E SUGESTÕES)
# =========================

@app.route('/enviar-feedback', methods=['POST'])
@login_required
def enviar_feedback():
    tipo = request.form.get('tipo')
    texto = request.form.get('texto')
    usuario_id = session['usuario_id']

    conn = conectar()
    conn.execute("INSERT INTO feedback (usuario_id, tipo, texto) VALUES (?, ?, ?)",
                 (usuario_id, tipo, texto))
    conn.commit()
    conn.close()
    return redirect(url_for('faq'))

@app.route("/admin/feedback/status/<int:id>")
@login_required
@cargo_required("admin")
def alterar_status_feedback(id):
    conn = conectar()
    feedback = conn.execute("SELECT usuario_id, status, tipo FROM feedback WHERE id = ?", (id,)).fetchone()
    
    if feedback:
        novo_status = 'resolvido' if feedback['status'] == 'aberto' else 'aberto'
        conn.execute("UPDATE feedback SET status = ? WHERE id = ?", (novo_status, id))
        conn.commit()
        
        if novo_status == 'resolvido':
            # Lógica para ajustar o gênero da mensagem
            if feedback['tipo'].lower() == 'bug':
                msg = f"Ei! O bug que você relatou foi corrigido. Obrigado por ajudar!"
            else:
                msg = f"Ei! A sugestão que você enviou foi implementada. Obrigado por ajudar!"
            
            criar_notificacao(feedback['usuario_id'], msg, link=url_for('faq'))
            
    conn.close()
    return redirect(url_for('servico_admin'))

@app.route("/admin/feedback/deletar/<int:id>")
@login_required
@cargo_required("admin")
def deletar_feedback(id):
    conn = conectar()
    conn.execute("DELETE FROM feedback WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('servico_admin'))

# =========================
# FÓRUNS
# =========================

@app.route("/forum_aluno")
@app.route("/forum_aluno/<int:id_editar>")
@login_required
@cargo_required("aluno")
def forum_aluno(id_editar=None):
    todos = listar_comentarios()
    usuario_id = session.get('usuario_id')
    usuario_cargo = session.get('cargo')
    tag_filtro = request.args.get('tag')
    termo_busca = request.args.get('busca', '').lower()
    
    comentarios_visiveis = []
    for c in todos:
        if c['destino'] == 'aluno' and c.get('pai_id') is None:
            pode_ver = (c['tag'] != 'admin') or (usuario_cargo == 'admin' or c['usuario_id'] == usuario_id)
            if pode_ver:
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                passa_na_busca = not termo_busca or termo_busca in c['texto'].lower()
                if passa_na_tag and passa_na_busca:
                    c['status'] = c.get('status', 'aberto')
                    c['total_respostas'] = len([r for r in todos if str(r.get('pai_id')) == str(c['id'])])
                    c['total_curtidas'] = contar_curtidas(c['id'])
                    c['usuario_ja_curtiu'] = usuario_curtiu(usuario_id, c['id'])
                    comentarios_visiveis.append(c)

    comentario_edit = buscar_comentario_por_id(id_editar) if id_editar else None
    return render_template("forumAluno.html", 
                            comentarios=comentarios_visiveis, 
                            comentario_selecionado=comentario_edit,
                            tag_ativa=tag_filtro,
                            busca_ativa=termo_busca)

@app.route("/forum_professor")
@app.route("/forum_professor/<int:id_editar>")
@login_required
@cargo_required("professor")
def forum_professor(id_editar=None):
    todos = listar_comentarios()
    usuario_id = session.get('usuario_id')
    usuario_cargo = session.get('cargo')
    tag_filtro = request.args.get('tag')
    termo_busca = request.args.get('busca', '').lower()
    
    comentarios_visiveis = []
    for c in todos:
        if c['destino'] == 'professor' and c.get('pai_id') is None:
            pode_ver = (c['tag'] != 'admin') or (usuario_cargo == 'admin' or c['usuario_id'] == usuario_id)
            if pode_ver:
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                passa_na_busca = not termo_busca or termo_busca in c['texto'].lower()
                if passa_na_tag and passa_na_busca:
                    c['status'] = c.get('status', 'aberto')
                    c['total_respostas'] = len([r for r in todos if str(r.get('pai_id')) == str(c['id'])])
                    c['total_curtidas'] = contar_curtidas(c['id'])
                    c['usuario_ja_curtiu'] = usuario_curtiu(usuario_id, c['id'])
                    comentarios_visiveis.append(c)

    comentario_edit = buscar_comentario_por_id(id_editar) if id_editar else None
    return render_template("forumProfessor.html", 
                            comentarios=comentarios_visiveis, 
                            comentario_selecionado=comentario_edit,
                            tag_ativa=tag_filtro,
                            busca_ativa=termo_busca)

# =========================
# PERFIL E ADMIN
# =========================

@app.route("/perfil")
@login_required
def perfil():
    origem = request.referrer or url_for('home')
    usuario_id = session.get("usuario_id")
    meus_comentarios = listar_comentarios_por_usuario(usuario_id)
    return render_template("perfil.html", 
                            nome=session.get("nome"), 
                            cargo=session.get("cargo"),
                            foto=session.get("foto") or "default.png",
                            comentarios=meus_comentarios,
                            url_retorno=origem)
    
@app.route("/upload_foto", methods=["POST"])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        return redirect(url_for('perfil'))
    
    arquivo = request.files['foto']
    
    if arquivo and arquivo.filename != '':
        # Definimos o nome do arquivo (mudei para .jpg para ser mais leve, mas .png funciona)
        novo_nome = f"user_{session['usuario_id']}.jpg"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome)
        
        # Abre a imagem original
        img = Image.open(arquivo.stream) 
        
        # Converte para RGB (necessário para salvar como JPEG ou remover transparências estranhas)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        # O PULO DO GATO: Redimensiona e corta centralizado em 300x300
        # Isso garante que a imagem seja um QUADRADO perfeito para o círculo do CSS
        tamanho_padrao = (300, 300)
        img = ImageOps.fit(img, tamanho_padrao, Image.Resampling.LANCZOS)
        
        # Salva com compressão para não pesar no seu PC/Servidor
        img.save(caminho, "JPEG", quality=85)
        
        atualizar_foto_usuario(session['usuario_id'], novo_nome)
        session['foto'] = novo_nome
        
    return redirect(url_for('perfil'))




@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/servico_admin")
@login_required
@cargo_required("admin")
def servico_admin():
    # 1. Mensagens da Coordenação
    todos = listar_comentarios()
    mensagens_privadas = [c for c in todos if c['tag'] == 'admin']

    # 2. Feedbacks e Contador
    conn = conectar()
    feedbacks = conn.execute("""
        SELECT f.*, u.nome 
        FROM feedback f 
        JOIN usuario u ON f.usuario_id = u.id 
        ORDER BY f.status ASC, f.data_criacao DESC
    """).fetchall()
    
    total_abertos = sum(1 for f in feedbacks if f['status'] == 'aberto')
    conn.close()

    return render_template("admin.html", 
                           comentarios=mensagens_privadas, 
                           feedbacks=feedbacks,
                           total_abertos=total_abertos)

@app.route("/sobreProjeto")
def sobre_projeto():
    return render_template("sobreprojeto.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

if __name__ == "__main__":
    app.run(debug=True)