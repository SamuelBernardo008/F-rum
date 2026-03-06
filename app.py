import os
from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from models.database import init_db
from models.usuario import buscar_usuario_por_email, verificar_senha, atualizar_foto_usuario
from models.comentario import (
    criar_comentario, 
    listar_comentarios, 
    excluir_comentario, 
    buscar_comentario_por_id, 
    atualizar_comentario,
    listar_comentarios_por_usuario
)

app = Flask(__name__)
app.secret_key = "123"

# Configurações de Upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria a pasta de uploads caso não exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializa o banco de dados
init_db()

# =========================
# DECORATORS (SEGURANÇA)
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
                if usuario_cargo == "aluno":
                    return redirect(url_for("forum_aluno"))
                elif usuario_cargo == "professor":
                    return redirect(url_for("forum_professor"))
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================
# ROTAS DE AUTENTICAÇÃO
# =========================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        cargo = session.get("cargo")
        return redirect(url_for("servico_admin" if cargo == "admin" else f"forum_{cargo}"))

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        usuario = buscar_usuario_por_email(email)

        if usuario and verificar_senha(usuario, senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["cargo"] = usuario["cargo"]
            # Carrega a foto do banco para a sessão (usa default se estiver vazio)
            session["foto"] = usuario["foto"] if usuario.get("foto") else "default.jpg"
            
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
# GESTÃO DE COMENTÁRIOS
# =========================

@app.route("/comentario", methods=["POST"])
@login_required
def adicionar_comentario():
    id_comentario = request.form.get("id_comentario")
    texto = request.form.get("texto")
    tag = request.form.get("tag")
    destino = request.form.get("origem")
    usuario_id = session.get("usuario_id")

    if texto and tag and destino:
        if id_comentario and id_comentario.strip():
            comentario = buscar_comentario_por_id(id_comentario)
            if comentario and (comentario['usuario_id'] == usuario_id or session.get('cargo') == 'admin'):
                atualizar_comentario(id_comentario, texto, tag)
        else:
            criar_comentario(texto, usuario_id, tag, destino)
    
    return redirect(url_for(f"forum_{destino}"))

@app.route("/comentario/deletar/<int:id>")
@login_required
def deletar_comentario(id):
    comentario = buscar_comentario_por_id(id)
    if comentario:
        if comentario['usuario_id'] == session.get("usuario_id") or session.get("cargo") == "admin":
            excluir_comentario(id)
    return redirect(request.referrer or url_for("home"))

# =========================
# FÓRUNS E FILTROS
# =========================

@app.route("/forumAluno")
@app.route("/forum_aluno/<int:id_editar>")
@login_required
def forum_aluno(id_editar=None):
    todos = listar_comentarios()
    usuario_id = session.get('usuario_id')
    usuario_cargo = session.get('cargo')
    
    tag_filtro = request.args.get('tag')
    termo_busca = request.args.get('busca', '').lower()
    
    comentarios_visiveis = []
    for c in todos:
        if c['destino'] == 'aluno':
            pode_ver = (c['tag'] != 'admin') or (usuario_cargo == 'admin' or c['usuario_id'] == usuario_id)
            if pode_ver:
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                passa_na_busca = not termo_busca or termo_busca in c['texto'].lower()
                if passa_na_tag and passa_na_busca:
                    comentarios_visiveis.append(c)

    comentario_edit = buscar_comentario_por_id(id_editar) if id_editar else None
    return render_template("forumAluno.html", 
                           comentarios=comentarios_visiveis, 
                           comentario_selecionado=comentario_edit,
                           tag_ativa=tag_filtro,
                           busca_ativa=termo_busca)

@app.route("/forumProfessor")
@app.route("/forumProfessor/<int:id_editar>")
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
        if c['destino'] == 'professor':
            pode_ver = (c['tag'] != 'admin') or (usuario_cargo == 'admin' or c['usuario_id'] == usuario_id)
            if pode_ver:
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                passa_na_busca = not termo_busca or termo_busca in c['texto'].lower()
                if passa_na_tag and passa_na_busca:
                    comentarios_visiveis.append(c)

    comentario_edit = buscar_comentario_por_id(id_editar) if id_editar else None
    return render_template("forumProfessor.html", 
                           nome=session.get("nome"),
                           comentarios=comentarios_visiveis, 
                           comentario_selecionado=comentario_edit,
                           tag_ativa=tag_filtro,
                           busca_ativa=termo_busca)

# =========================
# PERFIL E UPLOAD
# =========================

@app.route("/perfil")
@login_required
def perfil():
    usuario_id = session.get("usuario_id")
    meus_comentarios = listar_comentarios_por_usuario(usuario_id)
    return render_template("perfil.html", 
                           nome=session.get("nome"), 
                           cargo=session.get("cargo"),
                           foto=session.get("foto", "default.jpg"),
                           comentarios=meus_comentarios)

@app.route("/upload_foto", methods=["POST"])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        return redirect(url_for('perfil'))
    
    arquivo = request.files['foto']
    
    if arquivo and arquivo.filename != '':
        # Nome seguro: user_1_nome-da-foto.jpg
        extensao = arquivo.filename.rsplit('.', 1)[1].lower()
        novo_nome = f"user_{session['usuario_id']}.{extensao}"
        
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome)
        arquivo.save(caminho)
        
        # Atualiza no banco e na sessão
        atualizar_foto_usuario(session['usuario_id'], novo_nome)
        session['foto'] = novo_nome

    return redirect(url_for('perfil'))

# =========================
# PAINEL ADMIN E FAQ
# =========================

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