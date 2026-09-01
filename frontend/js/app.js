// Iniciar
document.getElementById('modal-tarefa').addEventListener('click', function(e) {
            if (e.target === this) fecharModal();
        });

        document.addEventListener('click', function(e) {
            const painel = document.getElementById('painel-notificacoes');
            const btnNotif = document.querySelector('.btn-notif');
            if (painel.classList.contains('ativo') && !painel.contains(e.target) && !btnNotif.contains(e.target)) {
                painel.classList.remove('ativo');
            }
        });

        document.getElementById('login-senha').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') fazerLogin();
        });
        document.getElementById('registo-senha').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') fazerRegisto();
        });

        if (token && utilizador) {
            entrarNoDashboard();
        }
