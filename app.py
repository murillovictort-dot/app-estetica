from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "segredo_super_seguro"

DB = "database.db"

# ---------------- BANCO ----------------
def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def criar_banco():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        login TEXT UNIQUE,
        senha TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        nome_cliente TEXT,
        telefone TEXT,
        data TEXT,
        hora TEXT,
        criado_em TEXT,
        FOREIGN KEY (clinica_id) REFERENCES clinicas(id)
    )
    """)

    # cria clínica padrão se não existir
    cur.execute("SELECT * FROM clinicas WHERE login='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO clinicas (nome, login, senha) VALUES (?,?,?)",
            ("Clínica Demo", "admin", "123")
        )

    con.commit()
    con.close()

criar_banco()

# ---------------- CLIENTE ----------------
@app.route("/", methods=["GET", "POST"])
def agendar():
    msg = ""
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]

        con = conectar()
        cur = con.cursor()

        cur.execute("SELECT id FROM clinicas LIMIT 1")
        clinica = cur.fetchone()

        cur.execute("""
            INSERT INTO agendamentos 
            (clinica_id, nome_cliente, telefone, data, hora, criado_em)
            VALUES (?,?,?,?,?,?)
        """, (
            clinica["id"],
            nome,
            telefone,
            data,
            hora,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ))

        con.commit()
        con.close()
        msg = "Agendamento realizado com sucesso!"

    return render_template("agendar.html", msg=msg)

# ---------------- LOGIN CLÍNICA ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""
    if request.method == "POST":
        login = request.form["login"]
        senha = request.form["senha"]

        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (login, senha)
        )
        clinica = cur.fetchone()
        con.close()

        if clinica:
            session["clinica_id"] = clinica["id"]
            return redirect("/dashboard")
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT * FROM agendamentos
        WHERE clinica_id=?
        ORDER BY data, hora
    """, (session["clinica_id"],))
    agendamentos = cur.fetchall()
    con.close()

    return render_template("dashboard.html", agendamentos=agendamentos)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
