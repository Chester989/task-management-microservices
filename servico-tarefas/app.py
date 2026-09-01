from flask import Flask, request, jsonify
import mysql.connector
import os
import time

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
                CREATE TABLE IF NOT EXISTS tarefas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    titulo VARCHAR(200) NOT NULL,
                    descricao TEXT,
                    estado ENUM('pendente', 'em_progresso', 'concluida') DEFAULT 'pendente',
                    data_limite DATE,
                    utilizador_id INT NOT NULL,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            ligacao.commit()
            cursor.close()
            ligacao.close()
            print("Tabela de tarefas inicializada com sucesso.")
            return
        except mysql.connector.Error as erro:
            print(f"Tentativa {tentativa + 1}: A aguardar pelo MariaDB... ({erro})")
            time.sleep(2)

    print("Erro: Nao foi possivel ligar ao MariaDB.")


@app.route("/tarefas", methods=["POST"])
def criar_tarefa():
    dados = request.get_json()

    if not dados or not dados.get("titulo") or not dados.get("utilizador_id"):
        return jsonify({"erro": "Campos 'titulo' e 'utilizador_id' sao obrigatorios."}), 400

    estado = dados.get("estado", "pendente")
    estados_validos = ["pendente", "em_progresso", "concluida"]
    if estado not in estados_validos:
        return jsonify({"erro": f"Estado invalido. Valores possiveis: {estados_validos}"}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()

        cursor.execute(
            """INSERT INTO tarefas (titulo, descricao, estado, data_limite, utilizador_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                dados["titulo"],
                dados.get("descricao", ""),
                estado,
                dados.get("data_limite"),
                dados["utilizador_id"]
            )
        )
        ligacao.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        ligacao.close()

        return jsonify({
            "mensagem": "Tarefa criada com sucesso.",
            "id": novo_id
        }), 201

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/tarefas", methods=["GET"])
def listar_tarefas():
    utilizador_id = request.args.get("utilizador_id")

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)

        if utilizador_id:
            cursor.execute(
                "SELECT * FROM tarefas WHERE utilizador_id = %s ORDER BY criado_em DESC",
                (utilizador_id,)
            )
        else:
            cursor.execute("SELECT * FROM tarefas ORDER BY criado_em DESC")

        tarefas = cursor.fetchall()
        cursor.close()
        ligacao.close()

        for t in tarefas:
            t["criado_em"] = str(t["criado_em"])
            t["atualizado_em"] = str(t["atualizado_em"])
            if t["data_limite"]:
                t["data_limite"] = str(t["data_limite"])

        return jsonify(tarefas), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/tarefas/<int:id_tarefa>", methods=["GET"])
def obter_tarefa(id_tarefa):
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tarefas WHERE id = %s", (id_tarefa,))
        tarefa = cursor.fetchone()
        cursor.close()
        ligacao.close()

        if not tarefa:
            return jsonify({"erro": "Tarefa nao encontrada."}), 404

        tarefa["criado_em"] = str(tarefa["criado_em"])
        tarefa["atualizado_em"] = str(tarefa["atualizado_em"])
        if tarefa["data_limite"]:
            tarefa["data_limite"] = str(tarefa["data_limite"])

        return jsonify(tarefa), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/tarefas/<int:id_tarefa>", methods=["PUT"])
def atualizar_tarefa(id_tarefa):
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Nenhum dado fornecido para atualizacao."}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()

        campos = []
        valores = []

        if "titulo" in dados:
            campos.append("titulo = %s")
            valores.append(dados["titulo"])
        if "descricao" in dados:
            campos.append("descricao = %s")
            valores.append(dados["descricao"])
        if "estado" in dados:
            estados_validos = ["pendente", "em_progresso", "concluida"]
            if dados["estado"] not in estados_validos:
                return jsonify({"erro": f"Estado invalido. Valores possiveis: {estados_validos}"}), 400
            campos.append("estado = %s")
            valores.append(dados["estado"])
        if "data_limite" in dados:
            campos.append("data_limite = %s")
            valores.append(dados["data_limite"])

        if not campos:
            return jsonify({"erro": "Nenhum campo valido para atualizar."}), 400

        valores.append(id_tarefa)
        query = f"UPDATE tarefas SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(query, valores)
        ligacao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            ligacao.close()
            return jsonify({"erro": "Tarefa nao encontrada."}), 404

        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Tarefa atualizada com sucesso."}), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/tarefas/<int:id_tarefa>", methods=["DELETE"])
def eliminar_tarefa(id_tarefa):
    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()
        cursor.execute("DELETE FROM tarefas WHERE id = %s", (id_tarefa,))
        ligacao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            ligacao.close()
            return jsonify({"erro": "Tarefa nao encontrada."}), 404

        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Tarefa eliminada com sucesso."}), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": f"Erro na base de dados: {str(erro)}"}), 500


@app.route("/saude", methods=["GET"])
def verificar_saude():
    return jsonify({"estado": "ativo", "servico": "tarefas"}), 200


if __name__ == "__main__":
    inicializar_bd()
    app.run(host="0.0.0.0", port=5003, debug=False)
