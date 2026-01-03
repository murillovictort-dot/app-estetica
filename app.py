from flask import Flask, request, redirect, session, render_template_string
import sqlite3, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "segredo_premium"

DB = "database.db"

# =======================
# BANCO
# =======================
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS clinicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            login TEXT UNIQUE,
            senha TEXT
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            clinica_id INTEGER,
            nome TEXT,
            telefone TEXT,
            dor TEXT,
            sugestao TEXT,
            criado_em TEXT
        );

        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinica_id INTEGER,
            cliente_codigo TEXT,
            data TEXT,
            hora TEXT
        );
        """)

# =======================
# ESTILO PREMIUM
# =======================
STYLE = """
<style>
body{
    background:#0b0b0b;
    color:#f5f5f5;
    font-family: 'Playfair Display', serif;
    margin:0;
}
.container{
    max-width:900px;
    margin:auto;
    padding:40px;
}
h1,h2,h3{ color:#d4af37; }
.card{
    background:#141414;
    border-radius:16px;
    padding:25px;
    margin-bottom:20px;
}
input,textarea,button{
    width:100%;
    padding:12px;
    margin:6px 0;
    border-radius:8px;
    border:1px solid #d4af37;
    background:#0e0e0e;
    color:white;
}
button{
    background:#d4af37;
    color:black;
    font-weight:bold;
    cursor:pointer;
}
.chat{
    background:#101010;
    border-radius:12px;
    padding:15px;
}
.assistente{
    color:#d4af37;
}
</style>
"""

# =======================
# HOME
# =======================
@app.route("/")
def home():
    return render_template_string(STYLE + """
    <div class="container">
        <h1>Plataforma Premium para Clínicas</h1>
        <p>Agendamento elegante, inteligente e organizado.</p>
    </div>
    """)

# =======================
# LINK ÚNICO DA CLÍNICA
# =======================
@app.route("/c/<login>", methods=["GET","POST"])
def clinica_publica(login):
    con = db()
    clinica = con.execute("SELECT * FROM clinicas WHERE login=?", (login,)).fetchone()
    if not clinica:
        return "Clínica não encontrada"

    resposta = ""
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        dor = request.form["dor"]
        data = request.form["data"]
        hora = request.form["hora"]

        conflito = con.execute(
            "SELECT * FROM agendamentos WHERE clinica_id=? AND data=? AND hora=?",
            (clinica["id"], data, hora)
        ).fetchone()

        if conflito:
            resposta = "Horário indisponível"
        else:
            sugestao = "Limpeza de pele premium"
            if "acne" in dor.lower(): sugestao = "Protocolo Antiacne"
            if "mancha" in dor.lower(): sugestao = "Clareamento Facial"
            if "flacidez" in dor.lower(): sugestao = "Bioestimulador de Colágeno"

            codigo = str(uuid.uuid4())[:8]

            con.execute("""
                INSERT INTO clientes (codigo, clinica_id, nome, telefone, dor, sugestao, criado_em)
                VALUES (?,?,?,?,?,?,?)
            """,(codigo, clinica["id"], nome, telefone, dor, sugestao, datetime.now()))

            con.execute("""
                INSERT INTO agendamentos (clinica_id, cliente_codigo, data, hora)
                VALUES (?,?,?,?)
            """,(clinica["id"], codigo, data, hora))

            con.commit()
            return f"Código da consulta: {codigo}"

    return render_template_string(STYLE + f"""
    <div class="container">
        <h1>{clinica['nome']}</h1>

        <div class="card chat">
            <p class="assistente">💬 Olá, sou a assistente da clínica. O que te incomoda na sua pele?</p>
        </div>

        <form method="POST" class="card">
            <input name="nome" placeholder="Seu nome" required>
            <input name="telefone" placeholder="Telefone" required>
            <textarea name="dor" placeholder="Conte sua queixa" required></textarea>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <button>Agendar</button>
        </form>

        <p>{resposta}</p>
    </div>
    """)

# =======================
# LOGIN DA CLÍNICA
# =======================
@app.route("/login", methods=["GET","POST"])
def login():
    erro=""
    if request.method=="POST":
        con=db()
        c=con.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (request.form["login"],request.form["senha"])
        ).fetchone()
        if c:
            session["cid"]=c["id"]
            return redirect("/dashboard")
        erro="Login inválido"

    return render_template_string(STYLE + f"""
    <div class="container">
        <div class="card">
            <h2>Login da Clínica</h2>
            <form method="POST">
                <input name="login" placeholder="Login">
                <input type="password" name="senha" placeholder="Senha">
                <button>Entrar</button>
            </form>
            <p>{erro}</p>
        </div>
    </div>
    """)

# =======================
# DASHBOARD DA CLÍNICA
# =======================
@app.route("/dashboard")
def dashboard():
    if "cid" not in session: return redirect("/login")
    con=db()
    cid=session["cid"]

    agenda = con.execute("""
        SELECT a.data,a.hora,c.nome
        FROM agendamentos a
        JOIN clientes c ON c.codigo=a.cliente_codigo
        WHERE a.clinica_id=?
        ORDER BY a.data,a.hora
    """,(cid,)).fetchall()

    clientes = con.execute(
        "SELECT * FROM clientes WHERE clinica_id=?",
        (cid,)
    ).fetchall()

    return render_template_string(STYLE + """
    <div class="container">
        <h2>Agenda por Horário</h2>
        {% for a in agenda %}
        <div class="card">{{a['data']}} {{a['hora']}} - {{a['nome']}}</div>
        {% endfor %}

        <h2>Relatórios de Clientes</h2>
        {% for c in clientes %}
        <div class="card">
            <b>{{c['nome']}}</b><br>
            Dor: {{c['dor']}}<br>
            Sugestão: {{c['sugestao']}}<br>
            Código: {{c['codigo']}}
        </div>
        {% endfor %}
    </div>
    """, agenda=agenda, clientes=clientes)

# =======================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
