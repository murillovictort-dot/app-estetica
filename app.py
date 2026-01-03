from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "segredo_super_seguro"

# ------------------ BANCO ------------------

def conectar():
    return sqlite3.connect("database.db")

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
        hora TEXT
    )
    """)

    # clínica de exemplo
    cur.execute("""
    INSERT OR IGNORE INTO clinicas (id, nome, login, senha)
    VALUES (1, 'Bella Skin', 'bella', '1234')
    """)

    con.commit()
    con.close()

criar_banco()

# ------------------ CLIENTE ------------------

@app.route("/", methods=["GET", "POST"])
def agendar():
    msg = ""

    if request.method == "POST":
        login_clinica = request.form["clinica"]
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]

        con = conectar()
        cur = con.cursor()

        cur.execute(
            "SELECT id FROM clinicas WHERE login=?",
            (login_clinica,)
        )
        clinica = cur.fetchone()

        if clinica:
            cur.execute("""
            INSERT INTO agendamentos 
            (clinica_id, nome_cliente, telefone, data, hora)
            VALUES (?, ?, ?, ?, ?)
            """, (clinica[0], nome, telefone, data, hora))
            con.commit()
            msg = "Agendamento realizado com sucesso!"
        else:
            msg = "Clínica não encontrada"

        con.close()

    return render_template("agendar.html", msg=msg)

# ------------------ LOGIN ------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        login = request.form["login"]
        senha = request.form["senha"]

        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT id FROM clinicas WHERE login=? AND senha=?",
            (login, senha)
        )
        clinica = cur.fetchone()
        con.close()

        if clinica:
            session["clinica_id"] = clinica[0]
            return redirect("/dashboard")
        else:
            erro = "Login ou senha inválidos"

    return render_template("login.html", erro=erro)

# ------------------ DASHBOARD ------------------

@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect("/login")

    clinica_id = session["clinica_id"]

    con = conectar()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("""
    SELECT nome_cliente, telefone, data, hora
    FROM agendamentos
    WHERE clinica_id=?
    ORDER BY data, hora
    """, (clinica_id,))

    agendamentos = cur.fetchall()
    con.close()

    return render_template("dashboard.html", agendamentos=agendamentos)

# ------------------ LOGOUT ------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------ START ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
