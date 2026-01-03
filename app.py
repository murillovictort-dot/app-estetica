from flask import Flask, request, redirect, session, render_template_string, g, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "segredo_ultra_secreto"

DATABASE = "database.db"

# =============================
# BANCO DE DADOS
# =============================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        login TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        nome TEXT,
        telefone TEXT,
        data TEXT,
        hora TEXT,
        dor TEXT,
        criado_em TEXT
    );
    """)
    db.commit()

@app.before_request
def before_request():
    init_db()

# =============================
# ESTILO PREMIUM
# =============================
STYLE = """
<style>
body {
    background: linear-gradient(135deg, #0e0e0e, #1a1a1a);
    color: #f5f5f5;
    font-family: 'Georgia', serif;
    padding: 40px;
}
h1, h2, h3 {
    color: #d4af37;
    letter-spacing: 1px;
}
input, textarea, button {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    background: #111;
    border: 1px solid #d4af37;
    color: white;
    border-radius: 6px;
}
button {
    background: #d4af37;
    color: black;
    font-weight: bold;
    cursor: pointer;
}
.box {
    max-width: 650px;
    margin: auto;
}
.card {
    border: 1px solid #333;
    padding: 14px;
    margin: 10px 0;
    border-radius: 8px;
}
.small {
    color: #aaa;
    font-size: 14px;
}
</style>
"""

# =============================
# HOME
# =============================
@app.route("/")
def home():
    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>Plataforma Premium de Clínicas</h1>
        <p>Agendamento inteligente e elegante</p>
        <a href="/login"><button>Login da Clínica</button></a>
    </div>
    """)

# =============================
# LOGIN DA CLÍNICA
# =============================
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""
    if request.method == "POST":
        db = get_db()
        clinica = db.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (request.form["login"], request.form["senha"])
        ).fetchone()

        if clinica:
            session["clinica_id"] = clinica["id"]
            return redirect("/dashboard")
        erro = "Login inválido"

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Login da Clínica</h2>
        <form method="POST">
            <input name="login" placeholder="Login" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button>Entrar</button>
        </form>
        <p style="color:red">{erro}</p>
    </div>
    """)

# =============================
# DASHBOARD
# =============================
@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    db = get_db()
    clinica = db.execute(
        "SELECT * FROM clinicas WHERE id=?",
        (session["clinica_id"],)
    ).fetchone()

    if not clinica:
        session.clear()
        return redirect("/login")

    ags = db.execute(
        "SELECT * FROM agendamentos WHERE clinica_id=? ORDER BY data, hora",
        (clinica["id"],)
    ).fetchall()

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>{clinica['nome']}</h2>
        <p class="small">Link da clínica:</p>
        <p><b>/c/{clinica['slug']}</b></p>

        <h3>Agenda</h3>
        {"".join([
            f"<div class='card'>{a['data']} {a['hora']} — {a['nome']}</div>"
            for a in ags
        ]) or "<p>Nenhum agendamento ainda</p>"}
    </div>
    """)

# =============================
# AGENDAMENTO (CLIENTE)
# =============================
@app.route("/c/<slug>", methods=["GET", "POST"])
def agendar(slug):
    db = get_db()
    clinica = db.execute(
        "SELECT * FROM clinicas WHERE slug=?",
        (slug,)
    ).fetchone()

    if not clinica:
        abort(404)

    erro = ""
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]
        dor = request.form["dor"]

        conflito = db.execute("""
            SELECT 1 FROM agendamentos
            WHERE clinica_id=? AND data=? AND hora=?
        """, (clinica["id"], data, hora)).fetchone()

        if conflito:
            erro = "Horário indisponível"
        else:
            db.execute("""
                INSERT INTO agendamentos
                (clinica_id, nome, telefone, data, hora, dor, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                clinica["id"], nome, telefone, data, hora, dor,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            db.commit()
            return redirect("/")

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>{clinica['nome']}</h1>
        <h3>Agendamento</h3>
        <form method="POST">
            <input name="nome" placeholder="Nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <textarea name="dor" placeholder="O que te incomoda?" required></textarea>
            <button>Agendar</button>
        </form>
        <p style="color:red">{erro}</p>
    </div>
    """)

# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

