import os
from PIL import Image  
from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps
from models.database import init_db
from models.usuario import buscar_usuario_por_email, verificar_senha, atualizar_foto_usuario
from models.comentario import (
    criar_comentario, 
    listar_comentarios, 
    excluir_comentario, 
    buscar_comentario_por_id, 
    atualizar_comentario,
    listar_comentarios_por_usuario,
    atualizar_status_comentario  # <--- Adicione esta no seu models
)

app = Flask(__name__)
app.secret_key = "123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

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
            # Novo comentário sempre nasce com status 'aberto'
            criar_comentario(texto, usuario_id, tag, destino, pai_id)
    
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
                    # Se o banco não tiver a coluna status ainda, define 'aberto'
                    c['status'] = c.get('status', 'aberto')
                    c['total_respostas'] = len([r for r in todos if str(r.get('pai_id')) == str(c['id'])])
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
        novo_nome = f"user_{session['usuario_id']}.png"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome)
        img = Image.open(arquivo)
        img.save(caminho, "PNG")
        atualizar_foto_usuario(session['usuario_id'], novo_nome)
        session['foto'] = novo_nome

    return redirect(url_for('perfil'))

@app.route("/servico_admin")
@login_required
@cargo_required("admin")
def servico_admin():
    todos = listar_comentarios()
    mensagens_privadas = [c for c in todos if c['tag'] == 'admin']
    return render_template("admin.html", comentarios=mensagens_privadas)

@app.route("/faq")
def faq():
    return render_template("faq.html")

if __name__ == "__main__":
    app.run(debug=True)