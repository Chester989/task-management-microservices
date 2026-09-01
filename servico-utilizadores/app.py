from flask import Flask, request, jsonify
import mysql.connector
import os
import time
from werkzeug.security import generate_password_hash

app = Flask(__name__)

BD_HOST = os.environ.get("BD_HOST", "mariadb")
BD_UTILIZADOR = os.environ.get("BD_UTILIZADOR", "root")
BD_SENHA = os.environ["BD_SENHA"]
BD_NOME = os.environ.get("BD_NOME", "gestao_tarefas")


def obter_ligacao():
    return mysql.connector.connect(
        host=BD_HOST,
        user=BD_UTILIZADOR,
        password=BD_SENHA,
        database=BD_NOME
    )


def inicializar_bd():
    for tentativa in range(30):
        try:
            ligacao = mysql.connector.connect(
                host=BD_HOST,
                user=BD_UTILIZADOR,
                password=BD_SENHA
            )
            cursor = ligacao.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {BD_NOME}")
            cursor.close()
            ligacao.close()

            ligacao = obter_ligacao()
            cursor = ligacao.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utilizadores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(150) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            ligacao.commit()
            cursor.close()
            ligacao.close()
            print("Base de dados inicializada com sucesso.")
            return
        except mysql.connector.Error as erro:
            print(f"Tentativa {tentativa + 1}: A aguardar pelo MariaDB... ({erro})")
            time.sleep(2)

    print("Erro: Nao foi possivel ligar ao MariaDB apos varias tentativas.")


def encriptar_senha(senha):
    return generate_password_hash(senha)


@app.route("/utilizadores", methods=["POST"])
def criar_utilizador():
    dados = request.get_json()

    if not dados or not dados.get("nome") or not dados.get("email") or not dados.get("senha"):
        return jsonify({"erro": "Campos 'nome', 'email' e 'senha' sao obrigatorios."}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()

        password_hash = encriptar_senha(dados["senha"])

        cursor.execute(
            "INSERT INTO utilizadores (nome, email, password_hash) VALUES (%s, %s, %s)",
            (dados["nome"], dados["email"], password_hash)
        )
        ligacao.commit()
        novo_id = cursor.lastrowid

        cursor.close()
        ligacao.close()

        return jsonify({
            "mensagem": "Utilizador criado com sucesso.",
            "id": novo_id
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({"erro": "Ja existe um utilizador com esse email."}), 409
    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/utilizadores", methods=["GET"])
def listar_utilizadores():
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, criado_em FROM utilizadores")
        utilizadores = cursor.fetchall()
        cursor.close()
        ligacao.close()

        for u in utilizadores:
            u["criado_em"] = str(u["criado_em"])

        return jsonify(utilizadores), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/utilizadores/<int:id_utilizador>", methods=["GET"])
def obter_utilizador(id_utilizador):
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nome, email, criado_em FROM utilizadores WHERE id = %s",
            (id_utilizador,)
        )
        utilizador = cursor.fetchone()
        cursor.close()
        ligacao.close()

        if not utilizador:
            return jsonify({"erro": "Utilizador nao encontrado."}), 404

        utilizador["criado_em"] = str(utilizador["criado_em"])
        return jsonify(utilizador), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/utilizadores/email/<email>", methods=["GET"])
def obter_utilizador_por_email(email):
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nome, email, password_hash FROM utilizadores WHERE email = %s",
            (email,)
        )
        utilizador = cursor.fetchone()
        cursor.close()
        ligacao.close()

        if not utilizador:
            return jsonify({"erro": "Utilizador nao encontrado."}), 404

        return jsonify(utilizador), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/utilizadores/<int:id_utilizador>", methods=["PUT"])
def atualizar_utilizador(id_utilizador):
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Nenhum dado fornecido para atualizacao."}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()

        campos = []
        valores = []

        if "nome" in dados:
            campos.append("nome = %s")
            valores.append(dados["nome"])
        if "email" in dados:
            campos.append("email = %s")
            valores.append(dados["email"])
        if "senha" in dados:
            campos.append("password_hash = %s")
            valores.append(encriptar_senha(dados["senha"]))

        if not campos:
            return jsonify({"erro": "Nenhum campo valido para atualizar."}), 400

        valores.append(id_utilizador)
        query = f"UPDATE utilizadores SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(query, valores)
        ligacao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            ligacao.close()
            return jsonify({"erro": "Utilizador nao encontrado."}), 404

        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Utilizador atualizado com sucesso."}), 200

    except mysql.connector.IntegrityError:
        return jsonify({"erro": "Ja existe um utilizador com esse email."}), 409
    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/utilizadores/<int:id_utilizador>", methods=["DELETE"])
def eliminar_utilizador(id_utilizador):
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()
        cursor.execute("DELETE FROM tarefas WHERE utilizador_id = %s", (id_utilizador,))
        cursor.execute("DELETE FROM notificacoes WHERE utilizador_id = %s", (id_utilizador,))
        cursor.execute("DELETE FROM utilizadores WHERE id = %s", (id_utilizador,))
        ligacao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            ligacao.close()
            return jsonify({"erro": "Utilizador nao encontrado."}), 404

        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Utilizador eliminado com sucesso."}), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/saude", methods=["GET"])
def verificar_saude():
    return jsonify({"estado": "ativo", "servico": "utilizadores"}), 200


if __name__ == "__main__":
    inicializar_bd()
    app.run(host="0.0.0.0", port=5002, debug=False)
