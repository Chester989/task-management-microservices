// comunicação com a API
async function pedidoAPI(rota, metodo = 'GET', dados = null) {
            const opcoes = {
                method: metodo,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (token) {
                opcoes.headers['Authorization'] = 'Bearer ' + token;
            }

            if (dados) {
                opcoes.body = JSON.stringify(dados);
            }

            try {
                const resposta = await fetch(API_URL + rota, opcoes);
                const resultado = await resposta.json();

                if (resposta.status === 401 && token) {
                    terminarSessao();
                    return null;
                }

                resultado._status = resposta.status;
                return resultado;

            } catch (erro) {
                console.error('Erro no pedido:', erro);
                return { erro: 'Erro de ligacao ao servidor. Verifique se o sistema esta a correr.', _status: 0 };
            }
        }

        function mostrarMensagem(elementoId, texto, tipo) {
            const el = document.getElementById(elementoId);
            el.textContent = texto;
            el.className = 'mensagem ' + tipo;

            if (tipo === 'sucesso') {
                setTimeout(() => { el.className = 'mensagem'; }, 5000);
            }
        }

        function traduzirEstado(estado) {
            const mapa = {
                'pendente': 'Pendente',
                'em_progresso': 'Em progresso',
                'concluida': 'Concluida'
            };
            return mapa[estado] || estado;
        }
