from flask import Flask, request, render_template_string

app = Flask(__name__)

# Armazena os agendamentos (em memória)
agendamentos = []

HTML_CLIENTE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Agendamento Clínica</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f4f8;
            padding: 20px;
        }
        .card {
            max-width: 500px;
            background: white;
            margin: auto;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            color: #2c3e50;
        }
        input, textarea, button {
            width: 100%;
            padding: 10px;
            margin-top: 6px;
            margin-bottom: 12px;
            border-radius: 5px;
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
        .msg {
            margin-top: 15px;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 5px;
            color: #2e7d32;
            text-align: center;
        }
    </style>
</head>

<body>
<div class="card">
    <h2>📅 Agendar Consulta</h2>

    <form method="post">
        <input name="nome" placeholder="Nome do paciente" required>
        <input name="procedimento" placeholder="Procedimento" required>
        <input type="date" name="data" required>
        <input type="time" name="hora" required>
        <textarea name="obs" placeholder="Observações (opcional)"></textarea>
        <button type="submit">Confirmar Agendamento</button>
    </form>

    {% if enviado %}
    <div class="msg">
        ✅ Agendamento enviado com sucesso.<br>
        A clínica entrará em contato para confirmar.
    </div>
    {% endif %}
</div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Agenda da Clínica</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f5;
            padding: 20px;
        }
        .card {
            max-width: 900px;
            background: white;
            margin: auto;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            color: #2c3e50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        th {
            background: #3498db;
            color: white;
        }
    </style>
</head>

<body>
<div class="card">
    <h2>📋 Agenda da Clínica</h2>

    {% if agendamentos %}
    <table>
        <tr>
            <th>Paciente</th>
            <th>Procedimento</th>
            <th>Data</th>
            <th>Horário</th>
            <th>Observações</th>
        </tr>
        {% for a in agendamentos %}
        <tr>
            <td>{{ a.nome }}</td>
            <td>{{ a.procedimento }}</td>
            <td>{{ a.data }}</td>
            <td>{{ a.hora }}</td>
            <td>{{ a.obs }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="text-align:center;">Nenhum agendamento ainda.</p>
    {% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def cliente():
    enviado = False
    if request.method == "POST":
        agendamentos.append({
            "nome": request.form.get("nome"),
            "procedimento": request.form.get("procedimento"),
            "data": request.form.get("data"),
            "hora": request.form.get("hora"),
            "obs": request.form.get("obs")
        })
        enviado = True

    return render_template_string(HTML_CLIENTE, enviado=enviado)

@app.route("/admin")
def admin():
    return render_template_string(HTML_ADMIN, agendamentos=agendamentos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
