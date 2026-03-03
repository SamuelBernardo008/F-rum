from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps
from models.database import init_db
from models.usuario import buscar_usuario_por_email, verificar_senha

app = Flask(__name__)
app.secret_key = "123" 

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
            
            # ADMIN tem acesso livre
            if usuario_cargo == "admin":
                return f(*args, **kwargs)
            
            if usuario_cargo != cargo_permitido:
                if usuario_cargo == "aluno":
                    return redirect(url_for("forum_aluno")) # Corrigido
                elif usuario_cargo == "professor":
                    return redirect(url_for("forum_professor")) # Corrigido
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
            return redirect(url_for("servico_admin")) # Corrigido
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
                return redirect(url_for("servico_admin")) # Corrigido
            elif usuario["cargo"] == "professor":
                return redirect(url_for("forum_professor")) # Corrigido
            else:
                return redirect(url_for("forum_aluno")) # Corrigido

        return render_template("login.html", erro="Email ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# ÁREAS RESTRITAS
# =========================

@app.route("/forumAluno")
@login_required
@cargo_required("aluno")
def forum_aluno(): # Nome da função: forum_aluno
    return render_template("forumAluno.html", nome=session.get("nome"))

@app.route("/forumProfessor")
@login_required
@cargo_required("professor")
def forum_professor(): # Nome da função: forum_professor
    return render_template("forumProfessor.html", nome=session.get("nome"))

@app.route("/servicoAdmin")
@login_required
@cargo_required("admin")
def servico_admin(): # Nome da função: servico_admin
    return render_template("admin.html", nome=session.get("nome"))

if __name__ == "__main__":
    app.run(debug=True)