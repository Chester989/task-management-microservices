// Gestão de notificações
function alternarNotificacoes() {
            const painel = document.getElementById('painel-notificacoes');
            painel.classList.toggle('ativo');

            if (painel.classList.contains('ativo')) {
                carregarNotificacoes();
            }
        }

        async function carregarNotificacoes() {
            const resultado = await pedidoAPI('/api/notificacoes');

            if (!resultado || !Array.isArray(resultado)) {
                document.getElementById('lista-notificacoes').innerHTML =
                    '<div class="sem-notificacoes">Sem notificacoes.</div>';
                return;
            }

            const badge = document.getElementById('badge-notif');
            const naoLidas = resultado.filter(n => !n.lida).length;

            if (naoLidas > 0) {
                badge.textContent = naoLidas;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }

            const container = document.getElementById('lista-notificacoes');

            if (resultado.length === 0) {
                container.innerHTML = '<div class="sem-notificacoes">Sem notificacoes.</div>';
                return;
            }

            container.innerHTML = resultado.map(n => `
                <div class="notificacao-item ${n.lida ? '' : 'nao-lida'}"
                     onclick="marcarNotificacaoLida(${n.id}, this)">
                    <div>${escaparHTML(n.mensagem)}</div>
                    <div class="data-notif">${n.criado_em}</div>
                </div>
            `).join('');
        }

        async function marcarNotificacaoLida(id, elemento) {
            await pedidoAPI('/api/notificacoes/' + id + '/lida', 'PUT');
            elemento.classList.remove('nao-lida');
            carregarNotificacoes();
        }
