from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps
from models.database import init_db
from models.usuario import buscar_usuario_por_email, verificar_senha
from models.comentario import criar_comentario, listar_comentarios, excluir_comentario, buscar_comentario_por_id, atualizar_comentario

app = Flask(__name__)
app.secret_key = "123"

# Inicializa o banco
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

            # ADMIN tem acesso total
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
# ROTAS PÚBLICAS
# =========================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        cargo = session.get("cargo")
        if cargo == "admin":
            return redirect(url_for("servico_admin"))
        if cargo == "professor":
            return redirect(url_for("forum_professor"))
        return redirect(url_for("forum_aluno"))

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = buscar_usuario_por_email(email)

        if usuario and verificar_senha(usuario, senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["cargo"] = usuario["cargo"]

            if usuario["cargo"] == "admin":
                return redirect(url_for("servico_admin"))
            elif usuario["cargo"] == "professor":
                return redirect(url_for("forum_professor"))
            else:
                return redirect(url_for("forum_aluno"))

        return render_template("login.html", erro="Email ou senha inválidos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# ROTA DE COMENTÁRIO AJUSTADA
# =========================

@app.route("/comentario", methods=["POST"])
@login_required
def adicionar_comentario():
    # 1. Pegamos todos os dados do formulário
    id_comentario = request.form.get("id_comentario")
    texto = request.form.get("texto")
    tag = request.form.get("tag")
    destino = request.form.get("origem")
    usuario_id = session.get("usuario_id")

    if id_comentario:  # Se existe um ID, é uma EDIÇÃO
        from models.comentario import buscar_comentario_por_id, atualizar_comentario
        
        # Verificação de segurança (opcional, mas recomendada)
        comentario = buscar_comentario_por_id(id_comentario)
        if comentario and comentario['usuario_id'] == usuario_id:
            # IMPORTANTE: Passe o texto E a tag para a função
            atualizar_comentario(id_comentario, texto, tag) 
            
    else:  # Se NÃO existe ID, é um comentário NOVO
        from models.comentario import criar_comentario
        if texto and tag and destino:
            criar_comentario(texto, usuario_id, tag, destino)

    return redirect(url_for(f"forum_{destino}"))

# =========================
# ÁREAS RESTRITAS (FILTROS AJUSTADOS)
# =========================

from flask import request

@app.route("/forumAluno")
@app.route("/forum_aluno/<int:id_editar>")
@login_required
def forum_aluno(id_editar=None):
    todos = listar_comentarios()
    usuario_id = session.get('usuario_id')
    nome_usuario = session.get('nome', '').lower()
    
    # PEGA OS FILTROS DA URL
    tag_filtro = request.args.get('tag')
    termo_busca = request.args.get('busca', '').lower() # Termo digitado na busca
    
    comentarios_visiveis = []
    
    for c in todos:
        if c['destino'] == 'aluno':
            # 1. REGRA DE PRIVACIDADE THAUANY
            pode_ver = False
            if c['tag'] != 'Thauany':
                pode_ver = True
            elif c['usuario_id'] == usuario_id or nome_usuario == 'thauany':
                pode_ver = True
            
            if pode_ver:
                # 2. FILTRO POR TAG
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                
                # 3. FILTRO POR BUSCA (procura no texto do comentário)
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
    nome_usuario = session.get('nome', '').lower()
    
    # --- CAPTURA OS FILTROS DA URL ---
    tag_filtro = request.args.get('tag')
    termo_busca = request.args.get('busca', '').lower() 
    
    comentarios_visiveis = []
    
    for c in todos:
        # 1. Filtra pelo destino correto
        if c['destino'] == 'professor':
            
            # 2. REGRA DE PRIVACIDADE THAUANY
            pode_ver = False
            if c['tag'] != 'Thauany':
                pode_ver = True
            elif c['usuario_id'] == usuario_id or nome_usuario == 'thauany':
                pode_ver = True
            
            # 3. APLICAÇÃO DOS FILTROS (TAG E BUSCA)
            if pode_ver:
                # Checa se bate com a tag escolhida (ou se não tem tag nenhuma selecionada)
                passa_na_tag = not tag_filtro or c['tag'] == tag_filtro
                
                # Checa se o termo pesquisado está no texto (ou se o campo está vazio)
                passa_na_busca = not termo_busca or termo_busca in c['texto'].lower()
                
                if passa_na_tag and passa_na_busca:
                    comentarios_visiveis.append(c)

    # Lógica para edição
    comentario_edit = buscar_comentario_por_id(id_editar) if id_editar else None

    return render_template("forumProfessor.html", 
                           nome=session.get("nome"),
                           comentarios=comentarios_visiveis, 
                           comentario_selecionado=comentario_edit,
                           tag_ativa=tag_filtro,  # Enviando para o HTML saber qual tag destacar
                           busca_ativa=termo_busca) # Enviando para manter o texto na barra de busca
    
    

@app.route("/comentario/editar/<int:id>", methods=["POST"])
@login_required
def editar_comentario(id):
    # Você precisará criar essa função buscar_comentario_por_id no seu models/comentario.py
    comentario = buscar_comentario_por_id(id) 
    
    if not comentario:
        return redirect(url_for("home"))

    # Regra: Só edita se for o dono
    if comentario['usuario_id'] == session.get("usuario_id"):
        novo_texto = request.form.get("texto")
        # Chamar função de update no banco
        atualizar_comentario(id, novo_texto)
    
    # Redireciona de volta para onde o usuário estava
    return redirect(request.referrer or url_for("home"))


@app.route("/comentario/deletar/<int:id>")
@login_required
def deletar_comentario(id):
    comentario = buscar_comentario_por_id(id)
    
    if not comentario:
        return redirect(url_for("home"))

    usuario_id = session.get("usuario_id")
    usuario_cargo = session.get("cargo")

    # Regra: É o dono OU é admin?
    if comentario['usuario_id'] == usuario_id or usuario_cargo == "admin":
        excluir_comentario(id)
    
    return redirect(request.referrer or url_for("home"))

@app.route("/servico_admin")
@login_required
@cargo_required("admin")
def servico_admin():
    from models.comentario import listar_comentarios
    # Busca todos os comentários do banco
    todos = listar_comentarios()
    
    # FILTRO: Só entram na lista os comentários com a tag 'Thauany'
    mensagens_privadas = [c for c in todos if c['tag'] == 'Thauany']
    
    return render_template("admin.html", comentarios=mensagens_privadas)

@app.route("/faq")
def faq():
    return render_template("faq.html")

# =========================
# START
# =========================

if __name__ == "__main__":
    app.run(debug=True)