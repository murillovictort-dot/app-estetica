from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def conectar():
    return sqlite3.connect("database.db")

# cria o banco
with conectar() as con:
    con.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefone TEXT,
        data TEXT,
        hora TEXT,
        procedimento TEXT
    )
    """)

@app.route("/", methods=["GET", "POST"])
def agendar():
    mensagem = ""
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        data = request.form["data"]
        hora = request.form["hora"]
        procedimento = request.form["procedimento"]

        con = conectar()
        conflito = con.execute(
            "SELECT * FROM agendamentos WHERE data=? AND hora=?",
            (data, hora)
        ).fetchone()

        if conflito:
            mensagem = "❌ Esse horário já está reservado"
        else:
            con.execute(
                "INSERT INTO agendamentos (nome, telefone, data, hora, procedimento) VALUES (?,?,?,?,?)",
                (nome, telefone, data, hora, procedimento)
            )
            con.commit()
            mensagem = "✅ Agendamento realizado com sucesso"

    return render_template("agendar.html", mensagem=mensagem)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
