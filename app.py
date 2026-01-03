from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h2>Agendamento Online</h2>
    <p>Use um link no formato:</p>
    <p><b>/clinica/NOME_DA_CLINICA</b></p>
    <p>Exemplo:</p>
    <a href='/clinica/ana'>/clinica/ana</a>
    """

# Armazena agendamentos separados por clínica
# Ex: {"clinica1": [ {dados}, {dados} ]}
agendamentos = {}

# -----------------------------
# PÁGINA PÚBLICA (CLIENTE)
# -----------------------------
HTML_CLIENTE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Agendamento - {{ clinica }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f4f8;
            padding: 20px;
        }
        .card {
            max-width: 420px;
            background: white;
            margin: auto;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        }
        h2 {
            text-align: center;
            color: #2c3e50;
        }
        input, textarea, button {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
            margin-bottom: 12px;
            border-radius: 6px;
            border: 1px solid #ccc;
        }
        button {
            background: #2ecc71;
            color: white;
            font-size: 16px;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #27ae60;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>Agendar na clínica {{ clinica }}</h2>
        <form method="POST">
            <input type="text" name="nome" placeholder="Seu nome" required>
            <input type="tel" name="telefone" placeholder="Telefone" required>
            <input type="date" name="data" required>
            <input type="time" name="hora" required>
            <textarea name="obs" placeholder="Observações (opcional)"></textarea>
            <button type="submit">Agendar</button>
        </form>
    </div>
</body>
</html>
"""

# -----------------------------
# PÁGINA DA CLÍNICA (INTERNA)
# -----------------------------
HTML_CLINICA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Agenda - {{ clinica }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #ecf0f1;
            padding: 20px;
        }
        h2 {
            text-align: center;
        }
        table {
            width: 100%;
            max-width: 900px;
            margin: auto;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ccc;
            text-align: center;
        }
        th {
            background: #34495e;
            color: white;
        }
    </style>
</head>
<body>
    <h2>Agenda da clínica {{ clinica }}</h2>

    <table>
        <tr>
            <th>Nome</th>
            <th>Telefone</th>
            <th>Data</th>
            <th>Hora</th>
            <th>Obs</th>
        </tr>

        {% for a in agendamentos %}
        <tr>
            <td>{{ a.nome }}</td>
            <td>{{ a.telefone }}</td>
            <td>{{ a.data }}</td>
            <td>{{ a.hora }}</td>
            <td>{{ a.obs }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# -----------------------------
# ROTA CLIENTE
# -----------------------------
@app.route("/clinica/<clinica>", methods=["GET", "POST"])
def pagina_cliente(clinica):
    if clinica not in agendamentos:
        agendamentos[clinica] = []

    if request.method == "POST":
        agendamentos[clinica].append({
            "nome": request.form["nome"],
            "telefone": request.form["telefone"],
            "data": request.form["data"],
            "hora": request.form["hora"],
            "obs": request.form.get("obs", "")
        })
        return redirect(url_for("pagina_cliente", clinica=clinica))

    return render_template_string(HTML_CLIENTE, clinica=clinica)

# -----------------------------
# ROTA DA CLÍNICA (AGENDA)
# -----------------------------
@app.route("/agenda/<clinica>")
def pagina_clinica(clinica):
    lista = agendamentos.get(clinica, [])
    return render_template_string(
        HTML_CLINICA,
        clinica=clinica,
        agendamentos=lista
    )

# -----------------------------
# INICIAR APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
