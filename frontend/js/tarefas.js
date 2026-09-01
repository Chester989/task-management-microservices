// dashboard, tarefas e criação/edição
function entrarNoDashboard() {
            document.getElementById('pagina-auth').style.display = 'none';
            document.getElementById('pagina-principal').style.display = 'block';
            document.getElementById('nome-utilizador').textContent = 'Ola, ' + utilizador.nome;
            carregarTarefas();
            carregarNotificacoes();
        }

        async function carregarTarefas() {
            const resultado = await pedidoAPI('/api/tarefas');

            if (!resultado) return;

            const container = document.getElementById('lista-tarefas');
            const semTarefas = document.getElementById('sem-tarefas');

            if (Array.isArray(resultado) && resultado.length > 0) {
                semTarefas.style.display = 'none';
                container.innerHTML = resultado.map(tarefa => `
                    <div class="cartao-tarefa ${tarefa.estado}">
                        <div class="info-tarefa">
                            <div class="titulo-tarefa">${escaparHTML(tarefa.titulo)}</div>
                            ${tarefa.descricao ? `<div class="descricao-tarefa">${escaparHTML(tarefa.descricao)}</div>` : ''}
                            <div class="meta-tarefa">
                                <span class="estado estado-${tarefa.estado}">${traduzirEstado(tarefa.estado)}</span>
                                ${tarefa.data_limite ? `<span>Prazo: ${tarefa.data_limite}</span>` : ''}
                                <span>Criada: ${tarefa.criado_em.split(' ')[0]}</span>
                            </div>
                        </div>
                        <div class="acoes-tarefa">
                            <button class="btn btn-principal" onclick="abrirModalEditar(${tarefa.id}, '${escaparJS(tarefa.titulo)}', '${escaparJS(tarefa.descricao || '')}', '${tarefa.estado}', '${tarefa.data_limite || ''}')">Editar</button>
                            <button class="btn btn-perigo" onclick="eliminarTarefa(${tarefa.id})">Apagar</button>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '';
                semTarefas.style.display = 'block';
            }
        }

        function escaparHTML(texto) {
            const el = document.createElement('div');
            el.textContent = texto;
            return el.innerHTML;
        }

        function escaparJS(texto) {
            return texto.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
        }

        function abrirModalCriar() {
            document.getElementById('modal-titulo').textContent = 'Nova Tarefa';
            document.getElementById('tarefa-id').value = '';
            document.getElementById('tarefa-titulo').value = '';
            document.getElementById('tarefa-descricao').value = '';
            document.getElementById('tarefa-estado').value = 'pendente';
            document.getElementById('tarefa-data').value = '';
            document.getElementById('msg-modal').className = 'mensagem';
            document.getElementById('modal-tarefa').classList.add('ativo');
        }

        function abrirModalEditar(id, titulo, descricao, estado, dataLimite) {
            document.getElementById('modal-titulo').textContent = 'Editar Tarefa';
            document.getElementById('tarefa-id').value = id;
            document.getElementById('tarefa-titulo').value = titulo;
            document.getElementById('tarefa-descricao').value = descricao;
            document.getElementById('tarefa-estado').value = estado;
            document.getElementById('tarefa-data').value = dataLimite;
            document.getElementById('msg-modal').className = 'mensagem';
            document.getElementById('modal-tarefa').classList.add('ativo');
        }

        function fecharModal() {
            document.getElementById('modal-tarefa').classList.remove('ativo');
        }

        async function guardarTarefa() {
            const id = document.getElementById('tarefa-id').value;
            const titulo = document.getElementById('tarefa-titulo').value.trim();
            const descricao = document.getElementById('tarefa-descricao').value.trim();
            const estado = document.getElementById('tarefa-estado').value;
            const dataLimite = document.getElementById('tarefa-data').value;

            if (!titulo) {
                mostrarMensagem('msg-modal', 'O titulo e obrigatorio.', 'erro');
                return;
            }

            const dados = { titulo, descricao, estado };
            if (dataLimite) {
                dados.data_limite = dataLimite;
            }

            let resultado;

            if (id) {
                resultado = await pedidoAPI('/api/tarefas/' + id, 'PUT', dados);
            } else {
                resultado = await pedidoAPI('/api/tarefas', 'POST', dados);
            }

            if (!resultado) return;

            if (resultado._status === 200 || resultado._status === 201) {
                fecharModal();
                carregarTarefas();
                mostrarMensagem('msg-dashboard', resultado.mensagem || 'Tarefa guardada.', 'sucesso');
            } else {
                mostrarMensagem('msg-modal', resultado.erro || 'Erro ao guardar tarefa.', 'erro');
            }
        }

        async function eliminarTarefa(id) {
            if (!confirm('Tem a certeza que quer apagar esta tarefa?')) {
                return;
            }

            const resultado = await pedidoAPI('/api/tarefas/' + id, 'DELETE');

            if (!resultado) return;

            if (resultado._status === 200) {
                carregarTarefas();
                mostrarMensagem('msg-dashboard', 'Tarefa eliminada.', 'sucesso');
            } else {
                mostrarMensagem('msg-dashboard', resultado.erro || 'Erro ao eliminar tarefa.', 'erro');
            }
        }
