from flask import Flask, request, redirect, session, g, jsonify
import sqlite3
from datetime import datetime
import uuid
import os

# ======================
# CONFIG
# ======================
app = Flask(__name__)
app.secret_key = "super_secret_key_123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

# ======================
# DATABASE
# ======================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        slug TEXT UNIQUE,
        login TEXT UNIQUE,
        senha TEXT
    );

    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        nome TEXT,
        telefone TEXT,
        data TEXT,
        hora TEXT,
        codigo TEXT,
        criado_em TEXT
    );
    """)

    db.commit()
    db.close()

with app.app_context():
    init_db()

# ======================
# HELPERS
# ======================
def clinica_logada():
    return "clinica_id" in session

# ======================
# ROTAS PUBLICAS
# ======================
@app.route("/")
def home():
    return "<h1>SaaS de Agendamento Online</h1><p>Use /c/slug-da-clinica</p>"

@app.route("/c/<slug>")
def pagina_clinica(slug):
    db = get_db()
    clinica = db.execute(
        "SELECT * FROM clinicas WHERE slug = ?",
        (slug,)
    ).fetchone()

    if not clinica:
        return "Clínica não encontrada", 404

    return f"""
    <h2>Agendar em {clinica['nome']}</h2>
    <form method="POST" action="/agendar/{slug}">
        <input name="nome" placeholder="Seu nome" required><br>
        <input name="telefone" placeholder="Telefone" required><br>
        <input name="data" type="date" required><br>
        <input name="hora" type="time" required><br>
        <button>Agendar</button>
    </form>
    """

@app.route("/agendar/<slug>", methods=["POST"])
def agendar(slug):
    db = get_db()
    clinica = db.execute(
        "SELECT id FROM clinicas WHERE slug = ?",
        (slug,)
    ).fetchone()

    if not clinica:
        return "Clínica inválida", 404

    codigo = str(uuid.uuid4())[:8]

    db.execute("""
        INSERT INTO agendamentos
        (clinica_id, nome, telefone, data, hora, codigo, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        clinica["id"],
        request.form["nome"],
        request.form["telefone"],
        request.form["data"],
        request.form["hora"],
        codigo,
        datetime.now().isoformat()
    ))

    db.commit()

    return f"""
    <h3>Agendamento confirmado!</h3>
    <p>Código: <b>{codigo}</b></p>
    """

# ======================
# AUTH CLINICA
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        clinica = db.execute("""
            SELECT * FROM clinicas
            WHERE login = ? AND senha = ?
        """, (
            request.form["login"],
            request.form["senha"]
        )).fetchone()

        if clinica:
            session["clinica_id"] = clinica["id"]
            return redirect("/dashboard")

        return "Login inválido"

    return """
    <h2>Login da Clínica</h2>
    <form method="POST">
        <input name="login" placeholder="Login"><br>
        <input name="senha" type="password" placeholder="Senha"><br>
        <button>Entrar</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ======================
# DASHBOARD CLINICA
# ======================
@app.route("/dashboard")
def dashboard():
    if not clinica_logada():
        return redirect("/login")

    db = get_db()
    agendamentos = db.execute("""
        SELECT nome, data, hora
        FROM agendamentos
        WHERE clinica_id = ?
        ORDER BY data, hora
    """, (session["clinica_id"],)).fetchall()

    html = "<h2>Dashboard</h2><ul>"
    for a in agendamentos:
        html += f"<li>{a['data']} {a['hora']} - {a['nome']}</li>"
    html += "</ul><a href='/logout'>Sair</a>"

    return html

# ======================
# CRIAR CLINICA (ADMIN)
# ======================
@app.route("/criar_clinica", methods=["POST"])
def criar_clinica():
    db = get_db()

    db.execute("""
        INSERT INTO clinicas (nome, slug, login, senha)
        VALUES (?, ?, ?, ?)
    """, (
        request.json["nome"],
        request.json["slug"],
        request.json["login"],
        request.json["senha"]
    ))

    db.commit()
    return jsonify({"status": "ok"})

# ======================
# START
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
