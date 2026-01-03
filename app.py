from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# Guarda os agendamentos por clínica
agendamentos = {}

# ----------------------------
# ROTA INICIAL (Render precisa)
# ----------------------------
@app.route("/")
def home():
    return """
    <h2>App de Agendamento Online</h2>
    <p>Exemplos de uso:</p>
    <ul>
        <li>/clinica/ana</li>
        <li>/agenda/ana</li>
        <li>/clinica/bella</li>
        <li>/agenda/bella</li>
    </ul>
    """

# ----------------------------
# HTML DO CLIENTE
# ----------------------------
HTML_CLIENTE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agendamento - {{ clinica }}</title>
</head>
<body>
    <h2>Agendar na Clínica {{ clinica }}</h2>

    <form method="POST">
        <input name="nome" placeholder="Nome" required><br><br>
        <input name="telefone" placeholder="Telefone" required><br><br>
        <input type="date" name="data" required><br><br>
        <input type="time" name="hora" required><br><br>
        <textarea name="obs" placeholder="Observações"></textarea><br><br>
        <button type="submit">Agendar</button>
    </form>
</body>
</html>
"""

# ----------------------------
# HTML DA CLÍNICA (AGENDA)
# ----------------------------
HTML_CLINICA = """
<!DOCTYPE html>
<html>
<head>
    <title>Agenda - {{ clinica }}</title>
</head>
<body>
    <h2>Agenda da Clínica {{ clinica }}</h2>

    {% if agendamentos %}
        <ul>
        {% for a in agendamentos %}
            <li>
                <b>{{ a.nome }}</b><br>
                Telefone: {{ a.telefone }}<br>
                Data: {{ a.data }} | Hora: {{ a.hora }}<br>
                Obs: {{ a.obs }}
                <hr>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p>Nenhum agendamento ainda.</p>
    {% endif %}
</body>
</html>
"""

# ----------------------------
# ROTA DO CLIENTE
# ----------------------------
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

# ----------------------------
# ROTA DA CLÍNICA (AGENDA)
# ----------------------------
@app.route("/agenda/<clinica>")
def pagina_clinica(clinica):
    lista = agendamentos.get(clinica, [])
    return render_template_string(
        HTML_CLINICA,
        clinica=clinica,
        agendamentos=lista
    )

# ----------------------------
# INICIAR APP
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
