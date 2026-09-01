from flask import Flask, request, jsonify
import mysql.connector
import os
import time
import threading
from datetime import datetime, timedelta

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
                CREATE TABLE IF NOT EXISTS notificacoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    utilizador_id INT NOT NULL,
                    mensagem TEXT NOT NULL,
                    lida BOOLEAN DEFAULT FALSE,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            ligacao.commit()
            cursor.close()
            ligacao.close()
            print("Tabela de notificacoes inicializada com sucesso.")
            return
        except mysql.connector.Error as erro:
            print(f"Tentativa {tentativa + 1}: A aguardar pelo MariaDB... ({erro})")
            time.sleep(2)

    print("Erro: Nao foi possivel ligar ao MariaDB.")


def verificar_prazos():
    while True:
        try:
            ligacao = obter_ligacao()
            cursor = ligacao.cursor(dictionary=True)

            amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            hoje = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT t.id, t.titulo, t.data_limite, t.utilizador_id
                FROM tarefas t
                WHERE t.estado != 'concluida'
                AND t.data_limite IS NOT NULL
                AND t.data_limite BETWEEN %s AND %s
                AND NOT EXISTS (
                    SELECT 1 FROM notificacoes n
                    WHERE n.mensagem LIKE CONCAT('%%tarefa "', t.titulo, '"%%prazo%%')
                    AND n.utilizador_id = t.utilizador_id
                    AND DATE(n.criado_em) = CURDATE()
                )
            """, (hoje, amanha))

            tarefas_proximas = cursor.fetchall()

            for tarefa in tarefas_proximas:
                mensagem = (
                    f'A tarefa "{tarefa["titulo"]}" tem o prazo a terminar em '
                    f'{tarefa["data_limite"]}. Nao te esquecas de a concluir!'
                )
                cursor.execute(
                    "INSERT INTO notificacoes (utilizador_id, mensagem) VALUES (%s, %s)",
                    (tarefa["utilizador_id"], mensagem)
                )

            ligacao.commit()
            cursor.close()
            ligacao.close()

            if tarefas_proximas:
                print(f"Criadas {len(tarefas_proximas)} notificacao(oes) de prazo.")

        except Exception as erro:
            print(f"Erro ao verificar prazos: {erro}")

        time.sleep(3600)


@app.route("/notificacoes/agendar", methods=["POST"])
def agendar_notificacao():
    dados = request.get_json()

    if not dados or not dados.get("utilizador_id"):
        return jsonify({"erro": "Dados insuficientes."}), 400

    titulo = dados.get("titulo", "Sem titulo")
    data_limite = dados.get("data_limite", "sem data")
    mensagem = f'Foi criada a tarefa "{titulo}" com prazo ate {data_limite}.'

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()
        cursor.execute(
            "INSERT INTO notificacoes (utilizador_id, mensagem) VALUES (%s, %s)",
            (dados["utilizador_id"], mensagem)
        )
        ligacao.commit()
        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Notificacao agendada."}), 201

    except mysql.connector.Error as erro:
        return jsonify({"erro": str(erro)}), 500


@app.route("/notificacoes", methods=["GET"])
def listar_notificacoes():
    utilizador_id = request.args.get("utilizador_id")

    if not utilizador_id:
        return jsonify({"erro": "Parametro 'utilizador_id' obrigatorio."}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM notificacoes WHERE utilizador_id = %s ORDER BY criado_em DESC",
            (utilizador_id,)
        )
        notificacoes = cursor.fetchall()
        cursor.close()
        ligacao.close()

        for n in notificacoes:
            n["criado_em"] = str(n["criado_em"])
            n["lida"] = bool(n["lida"])

        return jsonify(notificacoes), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": str(erro)}), 500


@app.route("/notificacoes/<int:id_notificacao>/lida", methods=["PUT"])
def marcar_como_lida(id_notificacao):
    utilizador_id = request.args.get("utilizador_id")
    if not utilizador_id:
        return jsonify({"erro": "Parametro 'utilizador_id' obrigatorio."}), 400

    try:
        ligacao = obter_ligacao()
        cursor = ligacao.cursor()
        cursor.execute(
            "UPDATE notificacoes SET lida = TRUE WHERE id = %s AND utilizador_id = %s",
            (id_notificacao, utilizador_id)
        )
        ligacao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            ligacao.close()
            return jsonify({"erro": "Notificacao nao encontrada."}), 404

        cursor.close()
        ligacao.close()

        return jsonify({"mensagem": "Notificacao marcada como lida."}), 200

    except mysql.connector.Error as erro:
        return jsonify({"erro": str(erro)}), 500


@app.route("/saude", methods=["GET"])
def verificar_saude():
    return jsonify({"estado": "ativo", "servico": "notificacoes"}), 200


if __name__ == "__main__":
    inicializar_bd()

    thread_prazos = threading.Thread(target=verificar_prazos, daemon=True)
    thread_prazos.start()
    print("Verificacao automatica de prazos iniciada.")

    app.run(host="0.0.0.0", port=5004, debug=False)
