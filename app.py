from flask import Flask, request, redirect, session, render_template_string, g
import sqlite3
from datetime import datetime

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
        nome TEXT,
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
        criado_em TEXT
    );

    CREATE TABLE IF NOT EXISTS dores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        dor TEXT,
        sugestao TEXT
    );
    """)
    db.commit()

# =============================
# ESTILO PREMIUM
# =============================
STYLE = """
<style>
body {
    background: #0e0e0e;
    color: #f5f5f5;
    font-family: 'Georgia', serif;
    padding: 40px;
}
h1, h2 {
    color: #d4af37;
}
input, textarea, button {
    width: 100%;
    padding: 10px;
    margin: 6px 0;
    background: #1a1a1a;
    border: 1px solid #d4af37;
    color: white;
}
button {
    font-weight: bold;
    cursor: pointer;
}
.box {
    max-width: 600px;
    margin: auto;
}
.card {
    border: 1px solid #333;
    padding: 12px;
    margin: 8px 0;
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
        <p>Sistema profissional de agendamento</p>
    </div>
    """)

# =============================
# AGENDAMENTO (CLIENTE)
# =============================
@app.route("/c/<login>", methods=["GET", "POST"])
def cliente(login):
    db = get_db()
    clinica = db.execute("SELECT * FROM clinicas WHERE login=?", (login,)).fetchone()
    if not clinica:
        return "Clínica não encontrada"

    sugestao = ""
    erro = ""

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]
        dor = request.form["dor"]

        conflito = db.execute(
            "SELECT * FROM agendamentos WHERE clinica_id=? AND data=? AND hora=?",
            (clinica["id"], data, hora)
        ).fetchone()

        if conflito:
            erro = "Horário indisponível"
        else:
            sugestao = "Limpeza de pele"
            if "acne" in dor.lower():
                sugestao = "Protocolo Antiacne"
            elif "mancha" in dor.lower():
                sugestao = "Clareamento Facial"
            elif "flacidez" in dor.lower():
                sugestao = "Bioestimulador de Colágeno"

            db.execute("""
                INSERT INTO agendamentos (clinica_id, nome, telefone, data, hora, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (clinica["id"], nome, telefone, data, hora, datetime.now()))

            db.execute("""
                INSERT INTO dores (clinica_id, dor, sugestao)
                VALUES (?, ?, ?)
            """, (clinica["id"], dor, sugestao))

            db.commit()
            return redirect("/")

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>{clinica['nome']}</h1>
        <h2>Agendamento</h2>
        <form method="POST">
            <input name="nome" placeholder="Nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <textarea name="dor" placeholder="O que te incomoda na sua pele?" required></textarea>
            <button>Agendar</button>
        </form>
        <p style="color:red">{erro}</p>
    </div>
    """)

# =============================
# LOGIN CLÍNICA
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
            <input name="login" placeholder="Login">
            <input type="password" name="senha" placeholder="Senha">
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
    cid = session["clinica_id"]

    ags = db.execute(
        "SELECT * FROM agendamentos WHERE clinica_id=? ORDER BY criado_em",
        (cid,)
    ).fetchall()

    dores = db.execute(
        "SELECT * FROM dores WHERE clinica_id=?",
        (cid,)
    ).fetchall()

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Agendamentos</h2>
        {''.join([f"<div class='card'>{a['data']} {a['hora']} - {a['nome']}</div>" for a in ags])}

        <h2>Dores dos Clientes</h2>
        {''.join([f"<div class='card'>{d['dor']}<br><b>Sugestão:</b> {d['sugestao']}</div>" for d in dores])}
    </div>
    """)

# =============================
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
