from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

DB = "database.db"

# =========================
# BANCO DE DADOS (AUTO FIX)
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Tabela clínicas
    c.execute("""
    CREATE TABLE IF NOT EXISTS clinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        slug TEXT UNIQUE,
        login TEXT UNIQUE,
        senha TEXT
    )
    """)

    # garante slug em bancos antigos
    try:
        c.execute("ALTER TABLE clinicas ADD COLUMN slug TEXT UNIQUE")
    except:
        pass

    # tabela clientes
    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clinica_id INTEGER,
        nome TEXT,
        codigo TEXT,
        data TEXT,
        hora TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# LOGIN CLÍNICA
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form["login"]
        senha = request.form["senha"]

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM clinicas WHERE login=? AND senha=?",
            (login, senha)
        )
        clinica = c.fetchone()
        conn.close()

        if clinica:
            session["clinica_id"] = clinica["id"]
            return redirect(url_for("dashboard"))

    return render_template("login.html")


# =========================
# DASHBOARD (CORRIGIDO)
# =========================
@app.route("/dashboard")
def dashboard():
    if "clinica_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT * FROM clinicas WHERE id=?",
        (session["clinica_id"],)
    )
    clinica = c.fetchone()

    if not clinica:
        conn.close()
        return redirect(url_for("login"))

    c.execute(
        "SELECT * FROM clientes WHERE clinica_id=? ORDER BY data, hora",
        (clinica["id"],)
    )
    clientes = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        clinica=clinica,
        clientes=clientes
    )


# =========================
# PÁGINA DA CLÍNICA (LINK ÚNICO)
# =========================
@app.route("/c/<slug>")
def clinica_publica(slug):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM clinicas WHERE slug=?", (slug,))
    clinica = c.fetchone()
    conn.close()

    if not clinica:
        return "Clínica não encontrada", 404

    return render_template("clinica.html", clinica=clinica)


# =========================
# AGENDAMENTO CLIENTE
# =========================
@app.route("/agendar/<slug>", methods=["POST"])
def agendar(slug):
    nome = request.form["nome"]
    data = request.form["data"]
    hora = request.form["hora"]
    codigo = os.urandom(4).hex()

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM clinicas WHERE slug=?", (slug,))
    clinica = c.fetchone()

    if not clinica:
        conn.close()
        return "Clínica inválida"

    # bloqueia horário duplicado
    c.execute("""
        SELECT * FROM clientes
        WHERE clinica_id=? AND data=? AND hora=?
    """, (clinica["id"], data, hora))

    if c.fetchone():
        conn.close()
        return "Horário já ocupado"

    c.execute("""
        INSERT INTO clientes (clinica_id, nome, codigo, data, hora)
        VALUES (?, ?, ?, ?, ?)
    """, (clinica["id"], nome, codigo, data, hora))

    conn.commit()
    conn.close()

    return f"Agendado com sucesso! Código: {codigo}"


# =========================
# CRIAR CLÍNICA (USAR 1 VEZ)
# =========================
@app.route("/_criar_clinica")
def criar_clinica():
    conn = get_db()
    c = conn.cursor()

    nome = "Clínica Ribello"
    slug = "ribello"
    login = "ribello"
    senha = "123456"

    try:
        c.execute("""
            INSERT INTO clinicas (nome, slug, login, senha)
            VALUES (?, ?, ?, ?)
        """, (nome, slug, login, senha))
        conn.commit()
        msg = "Clínica criada com sucesso"
    except:
        msg = "Clínica já existe"

    conn.close()
    return msg


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# START
# =========================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
