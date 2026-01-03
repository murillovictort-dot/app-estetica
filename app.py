from flask import Flask, request, redirect, session, render_template_string, g, url_for
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

    CREATE TABLE IF NOT EXISTS conversas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        mensagem TEXT,
        resposta TEXT,
        criado_em TEXT
    );
    """)
    db.commit()

# =============================
# ESTILO PREMIUM
# =============================
STYLE = """
<style>
body {
    background: #0b0b0b;
    color: #f5f5f5;
    font-family: 'Georgia', serif;
    padding: 40px;
}
h1, h2 {
    color: #d4af37;
    text-align: center;
}
input, textarea, button {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    background: #111;
    border: 1px solid #d4af37;
    color: white;
}
button {
    background: linear-gradient(90deg, #d4af37, #b8962e);
    font-weight: bold;
    cursor: pointer;
}
.box {
    max-width: 650px;
    margin: auto;
    border: 1px solid #222;
    padding: 30px;
}
.card {
    border-bottom: 1px solid #333;
    padding: 10px 0;
}
small {
    color: #aaa;
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
        <p style="text-align:center">Agendamento elegante e inteligente</p>
        <p style="text-align:center">
            <a href="/login" style="color:#d4af37">Login da clínica</a>
        </p>
    </div>
    """)

# =============================
# ADMIN - CRIAR CLÍNICA
# =============================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    msg = ""
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "INSERT INTO clinicas (nome, login, senha) VALUES (?, ?, ?)",
                (
                    request.form["nome"],
                    request.form["login"],
                    request.form["senha"]
                )
            )
            db.commit()
            msg = "Clínica criada com sucesso!"
        except:
            msg = "Erro: login já existe"

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Criar Clínica</h2>
        <form method="POST">
            <input name="nome" placeholder="Nome da clínica" required>
            <input name="login" placeholder="Login (ex: ribello)" required>
            <input name="senha" placeholder="Senha" required>
            <button>Criar</button>
        </form>
        <p>{msg}</p>
    </div>
    """)

# =============================
# AGENDAMENTO CLIENTE
# =============================
@app.route("/c/<login>", methods=["GET", "POST"])
def cliente(login):
    db = get_db()
    clinica = db.execute(
        "SELECT * FROM clinicas WHERE login=?",
        (login,)
    ).fetchone()

    if not clinica:
        return "Clínica não encontrada"

    erro = ""
    resposta = ""

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]
        mensagem = request.form["mensagem"]

        conflito = db.execute(
            "SELECT 1 FROM agendamentos WHERE clinica_id=? AND data=? AND hora=?",
            (clinica["id"], data, hora)
        ).fetchone()

        if conflito:
            erro = "Horário indisponível"
        else:
            if "acne" in mensagem.lower():
                resposta = "Indicamos protocolo antiacne premium."
            elif "mancha" in mensagem.lower():
                resposta = "Tratamento de clareamento avançado."
            else:
                resposta = "Avaliação dermatológica personalizada."

            db.execute("""
                INSERT INTO agendamentos
                (clinica_id, nome, telefone, data, hora, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (clinica["id"], nome, telefone, data, hora, datetime.now()))

            db.execute("""
                INSERT INTO conversas
                (clinica_id, mensagem, resposta, criado_em)
                VALUES (?, ?, ?, ?)
            """, (clinica["id"], mensagem, resposta, datetime.now()))

            db.commit()
            return redirect(url_for("cliente", login=login))

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>{clinica['nome']}</h1>
        <h2>Agendamento</h2>
        <form method="POST">
            <input name="nome" placeholder="Seu nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <textarea name="mensagem" placeholder="Conte suas queixas ou dúvidas" required></textarea>
            <button>Agendar</button>
        </form>
        <p style="color:red">{erro}</p>
        <p style="color:#d4af37">{resposta}</p>
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
# DASHBOARD CLÍNICA
# =============================
@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    db = get_db()
    cid = session["clinica_id"]

    ags = db.execute(
        "SELECT * FROM agendamentos WHERE clinica_id=? ORDER BY data, hora",
        (cid,)
    ).fetchall()

    chats = db.execute(
        "SELECT * FROM conversas WHERE clinica_id=? ORDER BY criado_em DESC",
        (cid,)
    ).fetchall()

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Agenda</h2>
        {''.join([f"<div class='card'>{a['data']} {a['hora']} - {a['nome']}</div>" for a in ags])}

        <h2>Relatório de Conversas</h2>
        {''.join([f"<div class='card'><small>{c['mensagem']}</small><br><b>{c['resposta']}</b></div>" for c in chats])}
    </div>
    """)

# ===== CRIAR CLÍNICA MANUALMENTE (USAR 1 VEZ) =====
@app.route('/_criar_clinica')
def criar_clinica_manual():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # cria tabela se não existir
    c.execute("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        slug TEXT UNIQUE,
        login TEXT,
        senha TEXT
    )
    """)

    # dados da clínica
    nome = "Clínica Ribello"
    slug = "ribello"
    login = "ribello"
    senha = "123456"

    try:
        c.execute(
            "INSERT INTO clinicas (nome, slug, login, senha) VALUES (?, ?, ?, ?)",
            (nome, slug, login, senha)
        )
        conn.commit()
        msg = "Clínica criada com sucesso"
    except sqlite3.IntegrityError:
        msg = "Clínica já existe"

    conn.close()
    return msg

# =============================
if __name__ == "__main__":
    with app.app_context():
        init_db()
