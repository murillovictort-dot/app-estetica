from flask import Flask, request, redirect, session, render_template_string, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "SEGREDO_SUPER_FORTE_123"

DATABASE = "database.db"

# =========================
# BANCO DE DADOS
# =========================
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e):
    d = g.pop("db", None)
    if d:
        d.close()

def init_db():
    d = db()
    d.executescript("""
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
        codigo TEXT,
        criado_em TEXT
    );

    CREATE TABLE IF NOT EXISTS conversas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        mensagem TEXT,
        sugestao TEXT,
        criado_em TEXT
    );
    """)
    d.commit()

# =========================
# ESTILO PREMIUM
# =========================
STYLE = """
<style>
body {
    background: linear-gradient(135deg,#0a0a0a,#1c1c1c);
    color: #f5f5f5;
    font-family: 'Playfair Display', serif;
    padding: 40px;
}
h1,h2,h3 { color: #d4af37; }
.box {
    max-width: 700px;
    margin: auto;
    background: #111;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 0 30px rgba(212,175,55,.2);
}
input, textarea, button {
    width: 100%;
    padding: 12px;
    margin: 6px 0;
    background: #1c1c1c;
    border: 1px solid #d4af37;
    color: white;
    border-radius: 8px;
}
button {
    font-weight: bold;
    background: #d4af37;
    color: black;
    cursor: pointer;
}
.card {
    border: 1px solid #333;
    padding: 12px;
    margin: 10px 0;
    border-radius: 10px;
}
.small { font-size: 14px; color: #ccc; }
</style>
"""

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>Plataforma Premium de Clínicas</h1>
        <p>Sistema de agendamento inteligente e elegante</p>
        <p class="small">Área da clínica: /login</p>
    </div>
    """)

# =========================
# CLIENTE - AGENDAMENTO
# =========================
@app.route("/c/<login>", methods=["GET","POST"])
def cliente(login):
    d = db()
    clinica = d.execute("SELECT * FROM clinicas WHERE login=?", (login,)).fetchone()
    if not clinica:
        return "Clínica não encontrada"

    erro = ""
    resposta = ""

    if request.method == "POST":
        nome = request.form["nome"]
        tel = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]
        msg = request.form["msg"]

        conflito = d.execute(
            "SELECT 1 FROM agendamentos WHERE clinica_id=? AND data=? AND hora=?",
            (clinica["id"], data, hora)
        ).fetchone()

        if conflito:
            erro = "❌ Horário indisponível"
        else:
            codigo = f"C{int(datetime.now().timestamp())}"

            if "acne" in msg.lower():
                resposta = "Recomendamos Protocolo Antiacne"
            elif "mancha" in msg.lower():
                resposta = "Indicamos Clareamento Facial"
            elif "flacidez" in msg.lower():
                resposta = "Bioestimulador de Colágeno"
            else:
                resposta = "Avaliação personalizada em consulta"

            d.execute("""
            INSERT INTO agendamentos
            (clinica_id,nome,telefone,data,hora,codigo,criado_em)
            VALUES (?,?,?,?,?,?,?)
            """,(clinica["id"],nome,tel,data,hora,codigo,datetime.now()))

            d.execute("""
            INSERT INTO conversas
            (clinica_id,mensagem,sugestao,criado_em)
            VALUES (?,?,?,?)
            """,(clinica["id"],msg,resposta,datetime.now()))

            d.commit()
            return f"<h2>Agendado com sucesso</h2>Código do cliente: <b>{codigo}</b>"

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h1>{clinica['nome']}</h1>
        <h3>Agendamento Premium</h3>
        <form method="POST">
            <input name="nome" placeholder="Nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <textarea name="msg" placeholder="Conte suas queixas ou dúvidas"></textarea>
            <button>Agendar</button>
        </form>
        <p style="color:red">{erro}</p>
        <p class="small">Assistente virtual responde automaticamente</p>
    </div>
    """)

# =========================
# LOGIN CLÍNICA
# =========================
@app.route("/login", methods=["GET","POST"])
def login():
    erro=""
    if request.method=="POST":
        d=db()
        c=d.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (request.form["login"],request.form["senha"])
        ).fetchone()
        if c:
            session["cid"]=c["id"]
            return redirect("/dashboard")
        erro="Login inválido"
    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Login da Clínica</h2>
        <form method="POST">
            <input name="login">
            <input type="password" name="senha">
            <button>Entrar</button>
        </form>
        <p style="color:red">{erro}</p>
    </div>
    """)

# =========================
# DASHBOARD CLÍNICA
# =========================
@app.route("/dashboard")
def dashboard():
    if "cid" not in session:
        return redirect("/login")
    d=db()
    cid=session["cid"]

    ags=d.execute(
        "SELECT * FROM agendamentos WHERE clinica_id=? ORDER BY data,hora",
        (cid,)
    ).fetchall()

    conv=d.execute(
        "SELECT * FROM conversas WHERE clinica_id=?",
        (cid,)
    ).fetchall()

    return render_template_string(f"""
    {STYLE}
    <div class="box">
        <h2>Agenda</h2>
        {''.join([f"<div class='card'>{a['data']} {a['hora']} - {a['nome']}</div>" for a in ags])}

        <h2>Diagnóstico dos Clientes</h2>
        {''.join([f"<div class='card'><b>Cliente:</b> {c['mensagem']}<br><b>Sugestão:</b> {c['sugestao']}</div>" for c in conv])}
    </div>
    """)

# =========================
# ADMIN
# =========================
ADMIN_USER="admin"
ADMIN_PASS="1234"

@app.route("/admin-login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form["u"]==ADMIN_USER and request.form["p"]==ADMIN_PASS:
            session["admin"]=True
            return redirect("/admin")
    return "<form method='POST'>Admin:<input name='u'>Senha:<input type='password' name='p'><button>Entrar</button></form>"

@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")
    msg=""
    if request.method=="POST":
        try:
            db().execute(
                "INSERT INTO clinicas (nome,login,senha) VALUES (?,?,?)",
                (request.form["nome"],request.form["login"],request.form["senha"])
            )
            db().commit()
            msg="Clínica criada!"
        except:
            msg="Erro: login já existe"
    return f"""
    <h2>Criar Clínica</h2>
    <form method='POST'>
        Nome:<input name='nome'>
        Login:<input name='login'>
        Senha:<input name='senha'>
        <button>Criar</button>
    </form>
    {msg}
    """

# =========================
if __name__=="__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
