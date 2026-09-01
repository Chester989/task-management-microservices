from datetime import datetime, timedelta
import os

from flask import Flask, request, jsonify
import jwt
import requests
from werkzeug.security import check_password_hash

app = Flask(__name__)

CHAVE_SECRETA = os.environ["JWT_SEGREDO"]
URL_UTILIZADORES = os.environ.get("URL_UTILIZADORES", "http://servico-utilizadores:5002")
DURACAO_TOKEN_HORAS = 24


def gerar_token(id_utilizador, email, nome):
    agora = datetime.utcnow()
    payload = {
        "id": id_utilizador,
        "email": email,
        "nome": nome,
        "exp": agora + timedelta(hours=DURACAO_TOKEN_HORAS),
        "iat": agora,
    }
    return jwt.encode(payload, CHAVE_SECRETA, algorithm="HS256")


def senha_valida(senha, password_hash):
    try:
        return check_password_hash(password_hash, senha)
    except ValueError:
        return False


@app.route("/auth/registar", methods=["POST"])
def registar():
    dados = request.get_json()

    if not dados or not dados.get("nome") or not dados.get("email") or not dados.get("senha"):
        return jsonify({"erro": "Campos 'nome', 'email' e 'senha' sao obrigatorios."}), 400

    try:
        resposta = requests.post(
            f"{URL_UTILIZADORES}/utilizadores",
            json={
                "nome": dados["nome"],
                "email": dados["email"],
                "senha": dados["senha"],
            },
            timeout=10,
        )
    except requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Erro ao comunicar com o servico de utilizadores: {erro}"}), 503

    if resposta.status_code != 201:
        return resposta.json(), resposta.status_code

    resultado = resposta.json()
    token = gerar_token(resultado["id"], dados["email"], dados["nome"])

    return jsonify({
        "mensagem": "Registo efetuado com sucesso.",
        "token": token,
        "utilizador": {
            "id": resultado["id"],
            "nome": dados["nome"],
            "email": dados["email"],
        },
    }), 201


@app.route("/auth/login", methods=["POST"])
def login():
    dados = request.get_json()

    if not dados or not dados.get("email") or not dados.get("senha"):
        return jsonify({"erro": "Campos 'email' e 'senha' sao obrigatorios."}), 400

    try:
        resposta = requests.get(
            f"{URL_UTILIZADORES}/utilizadores/email/{dados['email']}",
            timeout=10,
        )
    except requests.exceptions.RequestException as erro:
        return jsonify({"erro": f"Erro ao comunicar com o servico de utilizadores: {erro}"}), 503

    if resposta.status_code == 404:
        return jsonify({"erro": "Email ou senha incorretos."}), 401

    if resposta.status_code != 200:
        return jsonify({"erro": "Erro interno ao verificar credenciais."}), 500

    utilizador = resposta.json()
    if not senha_valida(dados["senha"], utilizador["password_hash"]):
        return jsonify({"erro": "Email ou senha incorretos."}), 401

    token = gerar_token(utilizador["id"], utilizador["email"], utilizador["nome"])

    return jsonify({
        "mensagem": "Login efetuado com sucesso.",
        "token": token,
        "utilizador": {
            "id": utilizador["id"],
            "nome": utilizador["nome"],
            "email": utilizador["email"],
        },
    }), 200


@app.route("/auth/verificar", methods=["POST"])
def verificar_token():
    dados = request.get_json()

    if not dados or not dados.get("token"):
        return jsonify({"erro": "Token nao fornecido."}), 400

    try:
        payload = jwt.decode(dados["token"], CHAVE_SECRETA, algorithms=["HS256"])
        return jsonify({
            "valido": True,
            "utilizador": {
                "id": payload["id"],
                "email": payload["email"],
                "nome": payload["nome"],
            },
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"valido": False, "erro": "Token expirado."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valido": False, "erro": "Token invalido."}), 401


@app.route("/saude", methods=["GET"])
def verificar_saude():
    return jsonify({"estado": "ativo", "servico": "autenticacao"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
