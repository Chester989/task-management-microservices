// Autenticação e gestão de sessão
function mostrarRegisto() {
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-registo').style.display = 'block';
            document.getElementById('msg-login').className = 'mensagem';
        }

        function mostrarLogin() {
            document.getElementById('form-registo').style.display = 'none';
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('msg-registo').className = 'mensagem';
        }

        async function fazerLogin() {
            const email = document.getElementById('login-email').value.trim();
            const senha = document.getElementById('login-senha').value;

            if (!email || !senha) {
                mostrarMensagem('msg-login', 'Preencha todos os campos.', 'erro');
                return;
            }

            const resultado = await pedidoAPI('/api/auth/login', 'POST', { email, senha });

            if (!resultado) return;

            if (resultado._status === 200) {
                token = resultado.token;
                utilizador = resultado.utilizador;
                localStorage.setItem('token', token);
                localStorage.setItem('utilizador', JSON.stringify(utilizador));
                entrarNoDashboard();
            } else {
                mostrarMensagem('msg-login', resultado.erro || 'Erro ao fazer login.', 'erro');
            }
        }

        async function fazerRegisto() {
            const nome = document.getElementById('registo-nome').value.trim();
            const email = document.getElementById('registo-email').value.trim();
            const senha = document.getElementById('registo-senha').value;

            if (!nome || !email || !senha) {
                mostrarMensagem('msg-registo', 'Preencha todos os campos.', 'erro');
                return;
            }

            const resultado = await pedidoAPI('/api/auth/registar', 'POST', { nome, email, senha });

            if (!resultado) return;

            if (resultado._status === 201) {
                token = resultado.token;
                utilizador = resultado.utilizador;
                localStorage.setItem('token', token);
                localStorage.setItem('utilizador', JSON.stringify(utilizador));
                entrarNoDashboard();
            } else {
                mostrarMensagem('msg-registo', resultado.erro || 'Erro ao registar.', 'erro');
            }
        }

        function terminarSessao() {
            token = null;
            utilizador = null;
            localStorage.removeItem('token');
            localStorage.removeItem('utilizador');
            document.getElementById('pagina-auth').style.display = 'flex';
            document.getElementById('pagina-principal').style.display = 'none';
            document.getElementById('login-email').value = '';
            document.getElementById('login-senha').value = '';
            mostrarLogin();
        }
