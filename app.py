from flask import Flask, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

# =========================
# BANCO DE DADOS
# =========================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE,
        login TEXT UNIQUE,
        senha TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        nome TEXT,
        telefone TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ROTAS BÁSICAS
# =========================

@app.route("/")
def home():
    return "🔥 App Estética ONLINE"

# =========================
# CRIAR CLÍNICA
# =========================

@app.route("/criar_clinica", methods=["GET", "POST"])
def criar_clinica():
    if request.method == "POST":
        nome = request.form["nome"]
        login = request.form["login"]
        senha = request.form["senha"]

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO clinicas (nome, login, senha) VALUES (?, ?, ?)",
                (nome, login, senha)
            )
            conn.commit()
            conn.close()
            return "✅ Clínica criada com sucesso"
        except:
            return "❌ Clínica já existe"

    return """
    <h2>Criar Clínica</h2>
    <form method="post">
        Nome: <input name="nome"><br>
        Login: <input name="login"><br>
        Senha: <input name="senha" type="password"><br>
        <button>Criar</button>
    </form>
    """

# =========================
# LOGIN DA CLÍNICA
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form["login"]
        senha = request.form["senha"]

        conn = get_db()
        clinica = conn.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (login, senha)
        ).fetchone()
        conn.close()

        if clinica:
            session["clinica_id"] = clinica["id"]
            return redirect("/dashboard")
        else:
            return "❌ Login inválido"

    return """
    <h2>Login da Clínica</h2>
    <form method="post">
        Login: <input name="login"><br>
        Senha: <input name="senha" type="password"><br>
        <button>Entrar</button>
    </form>
    """

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    return """
    <h1>Dashboard</h1>
    <a href="/clientes">Clientes</a><br>
    <a href="/logout">Sair</a>
    """

# =========================
# CLIENTES
# =========================

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if "clinica_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]

        conn.execute(
            "INSERT INTO clientes (clinica_id, nome, telefone) VALUES (?, ?, ?)",
            (session["clinica_id"], nome, telefone)
        )
        conn.commit()

    clientes = conn.execute(
        "SELECT * FROM clientes WHERE clinica_id=?",
        (session["clinica_id"],)
    ).fetchall()
    conn.close()

    lista = "".join([f"<li>{c['nome']} - {c['telefone']}</li>" for c in clientes])

    return f"""
    <h2>Clientes</h2>
    <form method="post">
        Nome: <input name="nome">
        Telefone: <input name="telefone">
        <button>Adicionar</button>
    </form>
    <ul>{lista}</ul>
    <a href="/dashboard">Voltar</a>
    """

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RENDER (ESSENCIAL)
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
