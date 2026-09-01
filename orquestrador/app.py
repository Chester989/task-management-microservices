from flask import Flask, request, jsonify
from flask_cors import CORS
import requests as http_requests
import os

app = Flask(__name__)
CORS(app)

URL_AUTENTICACAO = os.environ.get("URL_AUTENTICACAO", "http://servico-autenticacao:5001")
URL_UTILIZADORES = os.environ.get("URL_UTILIZADORES", "http://servico-utilizadores:5002")
URL_TAREFAS = os.environ.get("URL_TAREFAS", "http://servico-tarefas:5003")
URL_NOTIFICACOES = os.environ.get("URL_NOTIFICACOES", "http://servico-notificacoes:5004")


def verificar_token(req):
    cabecalho_auth = req.headers.get("Authorization")

    if not cabecalho_auth or not cabecalho_auth.startswith("Bearer "):
        return None

    token = cabecalho_auth.split(" ")[1]

    try:
        resposta = http_requests.post(
            f"{URL_AUTENTICACAO}/auth/verificar",
            json={"token": token},
            timeout=10
        )

        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get("valido"):
                return dados["utilizador"]

        return None

    except http_requests.exceptions.RequestException:
        return None


@app.route("/api/auth/registar", methods=["POST"])
def registar():
    try:
        resposta = http_requests.post(
            f"{URL_AUTENTICACAO}/auth/registar",
            json=request.get_json(),
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de autenticacao indisponivel: {str(erro)}"}), 503


@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        resposta = http_requests.post(
            f"{URL_AUTENTICACAO}/auth/login",
            json=request.get_json(),
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de autenticacao indisponivel: {str(erro)}"}), 503


@app.route("/api/utilizadores", methods=["GET"])
def listar_utilizadores():
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria. Faca login primeiro."}), 401

    try:
        resposta = http_requests.get(
            f"{URL_UTILIZADORES}/utilizadores",
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de utilizadores indisponivel: {str(erro)}"}), 503


@app.route("/api/utilizadores/<int:id_utilizador>", methods=["GET"])
def obter_utilizador(id_utilizador):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resposta = http_requests.get(
            f"{URL_UTILIZADORES}/utilizadores/{id_utilizador}",
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de utilizadores indisponivel: {str(erro)}"}), 503


@app.route("/api/utilizadores/<int:id_utilizador>", methods=["PUT"])
def atualizar_utilizador(id_utilizador):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    if utilizador["id"] != id_utilizador:
        return jsonify({"erro": "Nao tem permissao para editar este utilizador."}), 403

    try:
        resposta = http_requests.put(
            f"{URL_UTILIZADORES}/utilizadores/{id_utilizador}",
            json=request.get_json(),
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de utilizadores indisponivel: {str(erro)}"}), 503


@app.route("/api/utilizadores/<int:id_utilizador>", methods=["DELETE"])
def eliminar_utilizador(id_utilizador):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    if utilizador["id"] != id_utilizador:
        return jsonify({"erro": "Nao tem permissao para eliminar este utilizador."}), 403

    try:
        resposta = http_requests.delete(
            f"{URL_UTILIZADORES}/utilizadores/{id_utilizador}",
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de utilizadores indisponivel: {str(erro)}"}), 503


@app.route("/api/tarefas", methods=["POST"])
def criar_tarefa():
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados da tarefa nao fornecidos."}), 400

    dados["utilizador_id"] = utilizador["id"]

    try:
        resposta = http_requests.post(
            f"{URL_TAREFAS}/tarefas",
            json=dados,
            timeout=10
        )

        if resposta.status_code == 201 and dados.get("data_limite"):
            try:
                tarefa_id = resposta.json().get("id")
                http_requests.post(
                    f"{URL_NOTIFICACOES}/notificacoes/agendar",
                    json={
                        "tarefa_id": tarefa_id,
                        "utilizador_id": utilizador["id"],
                        "email": utilizador["email"],
                        "titulo": dados.get("titulo", ""),
                        "data_limite": dados["data_limite"]
                    },
                    timeout=5
                )
            except http_requests.exceptions.RequestException:
                pass

        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503


@app.route("/api/tarefas", methods=["GET"])
def listar_tarefas():
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resposta = http_requests.get(
            f"{URL_TAREFAS}/tarefas",
            params={"utilizador_id": utilizador["id"]},
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503


@app.route("/api/tarefas/<int:id_tarefa>", methods=["GET"])
def obter_tarefa(id_tarefa):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resposta = http_requests.get(
            f"{URL_TAREFAS}/tarefas/{id_tarefa}",
            timeout=10
        )

        if resposta.status_code == 200:
            tarefa = resposta.json()
            if tarefa["utilizador_id"] != utilizador["id"]:
                return jsonify({"erro": "Nao tem permissao para ver esta tarefa."}), 403

        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503


@app.route("/api/tarefas/<int:id_tarefa>", methods=["PUT"])
def atualizar_tarefa(id_tarefa):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resp_verificar = http_requests.get(
            f"{URL_TAREFAS}/tarefas/{id_tarefa}",
            timeout=10
        )

        if resp_verificar.status_code == 404:
            return jsonify({"erro": "Tarefa nao encontrada."}), 404

        tarefa = resp_verificar.json()
        if tarefa["utilizador_id"] != utilizador["id"]:
            return jsonify({"erro": "Nao tem permissao para editar esta tarefa."}), 403

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503

    try:
        resposta = http_requests.put(
            f"{URL_TAREFAS}/tarefas/{id_tarefa}",
            json=request.get_json(),
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503


@app.route("/api/tarefas/<int:id_tarefa>", methods=["DELETE"])
def eliminar_tarefa(id_tarefa):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resp_verificar = http_requests.get(
            f"{URL_TAREFAS}/tarefas/{id_tarefa}",
            timeout=10
        )

        if resp_verificar.status_code == 404:
            return jsonify({"erro": "Tarefa nao encontrada."}), 404

        tarefa = resp_verificar.json()
        if tarefa["utilizador_id"] != utilizador["id"]:
            return jsonify({"erro": "Nao tem permissao para eliminar esta tarefa."}), 403

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503

    try:
        resposta = http_requests.delete(
            f"{URL_TAREFAS}/tarefas/{id_tarefa}",
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Servico de tarefas indisponivel: {str(erro)}"}), 503


@app.route("/api/notificacoes", methods=["GET"])
def listar_notificacoes():
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resposta = http_requests.get(
            f"{URL_NOTIFICACOES}/notificacoes",
            params={"utilizador_id": utilizador["id"]},
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException:
        return jsonify([]), 200


@app.route("/api/notificacoes/<int:id_notificacao>/lida", methods=["PUT"])
def marcar_notificacao_lida(id_notificacao):
    utilizador = verificar_token(request)
    if not utilizador:
        return jsonify({"erro": "Autenticacao necessaria."}), 401

    try:
        resposta = http_requests.put(
            f"{URL_NOTIFICACOES}/notificacoes/{id_notificacao}/lida",
            params={"utilizador_id": utilizador["id"]},
            timeout=10
        )
        return resposta.json(), resposta.status_code

    except http_requests.exceptions.RequestException:
        return jsonify({"erro": "Servico de notificacoes indisponivel."}), 503


@app.route("/api/saude", methods=["GET"])
def verificar_saude():
    estado = {"orquestrador": "ativo"}

    servicos = {
        "autenticacao": URL_AUTENTICACAO,
        "utilizadores": URL_UTILIZADORES,
        "tarefas": URL_TAREFAS,
        "notificacoes": URL_NOTIFICACOES
    }

    for nome, url in servicos.items():
        try:
            resposta = http_requests.get(f"{url}/saude", timeout=3)
            if resposta.status_code == 200:
                estado[nome] = "ativo"
            else:
                estado[nome] = "erro"
        except http_requests.exceptions.RequestException:
            estado[nome] = "indisponivel"

    return jsonify(estado), 200


@app.route("/", methods=["GET"])
def raiz():
    return jsonify({
        "projeto": "Sistema de Gestao de Tarefas",
        "versao": "1.0",
        "autores": ["Joao Silva", "Joao Patrocinio", "Joao Maravilhoso"],
        "endpoints": {
            "auth": "/api/auth/registar, /api/auth/login",
            "utilizadores": "/api/utilizadores",
            "tarefas": "/api/tarefas",
            "notificacoes": "/api/notificacoes",
            "saude": "/api/saude"
        }
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
