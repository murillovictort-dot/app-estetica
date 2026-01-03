from flask import Flask, request, redirect, session, render_template_string, g
import sqlite3
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "cliniquesecret"

DATABASE = "database.db"

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
    db = get_db()
    db.executescript("""
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

# ======================
# ESTILO PREMIUM
# ======================
STYLE = """
<style>
body {
    background: linear-gradient(120deg, #0f0f0f, #1a1a1a);
    color: #fff;
    font-family: 'Segoe UI', sans-serif;
}
.container {
    max-width: 420px;
    margin: 60px auto;
    background: #111;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 0 30px rgba(212,175,55,0.2);
}
h1,h2 {
    color: #d4af37;
    text-align: center;
}
input, button {
    width: 100%;
    padding: 12px;
    margin-top: 10px;
    background: #1c1c1c;
    border: 1px solid #d4af37;
    color: white;
    border-radius: 6px;
}
button {
    cursor: pointer;
    font-weight: bold;
}
.card {
    background: #1a1a1a;
    padding: 10px;
    border-radius: 6px;
    margin-top: 10px;
}
small {
    color: #aaa;
}
</style>
"""

# ======================
# HOME
# ======================
@app.route("/")
def home():
    return render_template_string(f"""
    {STYLE}
    <div class="container">
        <h1>CLINIQUE</h1>
        <p style="text-align:center;">Agendamento inteligente para clínicas modernas</p>
        <p style="text-align:center;"><small>Área do cliente é acessada pelo link da clínica</small></p>
        <a href="/login"><button>Login da Clínica</button></a>
    </div>
    """)

# ======================
# CLIENTE
# ======================
@app.route("/c/<slug>", methods=["GET", "POST"])
def cliente(slug):
    db = get_db()
    clinica = db.execute("SELECT * FROM clinicas WHERE slug=?", (slug,)).fetchone()
    if not clinica:
        return "Clínica não encontrada"

    erro = ""
    codigo = None

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]

        conflito = db.execute("""
            SELECT * FROM agendamentos
            WHERE clinica_id=? AND data=? AND hora=?
        """, (clinica["id"], data, hora)).fetchone()

        if conflito:
            erro = "Horário indisponível"
        else:
            codigo = str(uuid.uuid4())[:8]
            db.execute("""
                INSERT INTO agendamentos
                (clinica_id, nome, telefone, data, hora, codigo, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (clinica["id"], nome, telefone, data, hora, codigo, datetime.now()))
            db.commit()

    return render_template_string(f"""
    {STYLE}
    <div class="container">
        <h2>{clinica['nome']}</h2>
        <form method="POST">
            <input name="nome" placeholder="Seu nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <button>Agendar</button>
        </form>
        <p style="color:red;">{erro}</p>
        {"<div class='card'>Consulta confirmada<br><b>Código:</b> "+codigo+"</div>" if codigo else ""}
    </div>
    """)

# ======================
# LOGIN CLÍNICA
# ======================
@app.route("/login", methods=["GET","POST"])
def login():
    erro = ""
    if request.method == "POST":
        db = get_db()
        c = db.execute("""
            SELECT * FROM clinicas
            WHERE login=? AND senha=?
        """, (request.form["login"], request.form["senha"])).fetchone()
        if c:
            session["clinica_id"] = c["id"]
            return redirect("/dashboard")
        erro = "Login inválido"

    return render_template_string(f"""
    {STYLE}
    <div class="container">
        <h2>Login da Clínica</h2>
        <form method="POST">
            <input name="login" placeholder="Login">
            <input type="password" name="senha" placeholder="Senha">
            <button>Entrar</button>
        </form>
        <p style="color:red;">{erro}</p>
    </div>
    """)

# ======================
# DASHBOARD
# ======================
@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    db = get_db()
    cid = session["clinica_id"]

    ags = db.execute("""
        SELECT * FROM agendamentos
        WHERE clinica_id=?
        ORDER BY data, hora
    """, (cid,)).fetchall()

    return render_template_string(f"""
    {STYLE}
    <div class="container">
        <h2>Agenda</h2>
        {''.join([f"<div class='card'>{a['data']} {a['hora']} - {a['nome']}</div>" for a in ags])}
    </div>
    """)

# ======================
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
