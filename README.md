# Sistema de Gestão de Tarefas com Microsserviços

**Unidade Curricular:** Arquitetura e Desenvolvimento de Microsserviços  
**Autores:** João Silva, João Patrocínio, João Maravilhoso

---

## Descrição

Este projeto implementa um sistema de gestão de tarefas com microsserviços. O utilizador pode criar conta, iniciar sessão e gerir tarefas.

Foi usada uma arquitetura com orquestrador: o cliente comunica com o orquestrador e este encaminha os pedidos para os servicos internos.

## Arquitetura

O sistema e composto pelos seguintes microsservicos, cada um a correr no seu proprio contentor Docker:

| Servico | Porta | Descricao |
|---------|-------|-----------|
| **Orquestrador (FM01)** | 5000 | Gateway central. Recebe todos os pedidos e reencaminha para os servicos corretos. Verifica a autenticacao. |
| **Autenticacao (FM02)** | 5001 interno | Registo e login de utilizadores com JWT. |
| **Utilizadores (FM03)** | 5002 interno | CRUD de contas de utilizador. |
| **Tarefas (FM04)** | 5003 interno | CRUD de tarefas. |
| **Notificacoes (FA01)** | 5004 interno | Notificacoes de prazos (funcionalidade extra). |
| **Frontend (FA02)** | 8080 | Interface web para interacao com o sistema (funcionalidade extra). |
| **MariaDB** | 3306 interno | Base de dados relacional. |

### Diagrama da Arquitetura

```
              Cliente (curl / Postman / Frontend)
                          |
                          v
                   +-------------+
                   | Orquestrador|  (FM01 - porta 5000)
                   |  (Gateway)  |
                   +------+------+
                     |    |    |
          +----------+    |    +----------+
          |               |               |
          v               v               v
   +------------+  +------------+  +------------+  +-------------+
   |Autenticacao|  |Utilizadores|  |  Tarefas   |  |Notificacoes |
   |   (FM02)   |  |   (FM03)   |  |   (FM04)   |  |   (FA01)    |
   +------------+  +------+-----+  +------+-----+  +------+------+
                          |               |               |
                          v               v               v
                   +------------------------------------+
                   |            MariaDB                  |
                   +------------------------------------+
```

## Tecnologias

- **Linguagem:** Python 3.11
- **Framework:** Flask
- **Base de dados:** MariaDB 10.11
- **Autenticacao:** JSON Web Tokens (JWT) com PyJWT
- **Passwords:** hash com Werkzeug
- **Contentorizacao:** Docker
- **Orquestracao:** Kubernetes (Minikube)
- **Comunicacao:** REST (Request/Response)

## Pre-requisitos

- Docker e Docker Compose instalados
- Minikube instalado (para deploy em Kubernetes)
- kubectl instalado
- Python 3.11+ (apenas para desenvolvimento local)

## Como correr

### Opção 1: Docker Compose

```bash
# Preparar as variáveis locais
cp .env.example .env

# Arrancar todos os servicos
docker-compose up --build

# O sistema fica disponivel em http://localhost:5000
# O frontend fica disponivel em http://localhost:8080
```

Para parar:
```bash
docker-compose down
```

### Opção 2: Minikube (Kubernetes)

```bash
# Criar o manifesto local de segredos e substituir os valores de exemplo
cp kubernetes/segredos.example.yaml kubernetes/segredos.yaml

# Dar permissões ao script
chmod +x scripts/deploy-minikube.sh

# Correr o script de deploy
./scripts/deploy-minikube.sh

# O script deixa a API em http://localhost:5000
# e o frontend em http://localhost:8080
```

Para limpar:
```bash
kubectl delete -f kubernetes/
```

## Endpoints da API

Todos os pedidos sao feitos ao orquestrador (porta 5000). As rotas protegidas requerem o cabecalho `Authorization: Bearer <token>`.

### Autenticacao

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/auth/registar` | Registar novo utilizador |
| POST | `/api/auth/login` | Fazer login |

**Exemplo de registo:**
```bash
curl -X POST http://localhost:5000/api/auth/registar \
  -H "Content-Type: application/json" \
  -d '{"nome": "Joao Silva", "email": "joao@email.com", "senha": "123456"}'
```

**Exemplo de login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "joao@email.com", "senha": "123456"}'
```

### Utilizadores (rotas protegidas)

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/utilizadores` | Listar todos os utilizadores |
| GET | `/api/utilizadores/:id` | Obter utilizador por ID |
| PUT | `/api/utilizadores/:id` | Atualizar utilizador |
| DELETE | `/api/utilizadores/:id` | Eliminar utilizador |

### Tarefas (rotas protegidas)

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/tarefas` | Listar tarefas do utilizador |
| POST | `/api/tarefas` | Criar nova tarefa |
| GET | `/api/tarefas/:id` | Obter tarefa por ID |
| PUT | `/api/tarefas/:id` | Atualizar tarefa |
| DELETE | `/api/tarefas/:id` | Eliminar tarefa |

**Exemplo de criacao de tarefa:**
```bash
curl -X POST http://localhost:5000/api/tarefas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"titulo": "Acabar o relatorio", "descricao": "Terminar o relatorio de ADM", "estado": "pendente", "data_limite": "2026-05-15"}'
```

### Notificacoes (rotas protegidas - funcionalidade extra)

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/notificacoes` | Listar notificacoes |
| PUT | `/api/notificacoes/:id/lida` | Marcar notificacao como lida |

### Estado do sistema

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/saude` | Verificar estado de todos os servicos |

## Estrutura do Projeto

```
projeto-adm/
├── orquestrador/            # FM01 - Servico Orquestrador
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── servico-autenticacao/    # FM02 - Servico de Autenticacao
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── servico-utilizadores/    # FM03 - Servico de Utilizadores
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── servico-tarefas/         # FM04 - Servico de Tarefas
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── servico-notificacoes/    # FA01 - Notificacoes (extra)
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # FA02 - Interface Web (extra)
│   ├── index.html
│   └── Dockerfile
├── kubernetes/              # Manifests para Minikube
│   ├── segredos.yaml
│   ├── mariadb.yaml
│   ├── orquestrador.yaml
│   ├── servico-autenticacao.yaml
│   ├── servico-utilizadores.yaml
│   ├── servico-tarefas.yaml
│   ├── servico-notificacoes.yaml
│   └── frontend.yaml
├── scripts/
│   └── deploy-minikube.sh   # Script de deploy
├── docker-compose.yml
└── README.md
```

## Notas

- Cada microsservico corre no seu proprio contentor Docker, conforme indicado no enunciado.
- A comunicacao entre servicos e feita via HTTP REST (Request/Response).
- O orquestrador funciona como ponto de entrada unico e reencaminha os pedidos.
- A autenticacao utiliza JWT com validade de 24 horas.
- As passwords sao guardadas com hash gerado pelo Werkzeug.
- No Docker Compose, apenas o orquestrador e o frontend ficam expostos ao exterior.
- O servico de notificacoes verifica automaticamente (de hora a hora) se existem tarefas com prazo proximo e cria notificacoes.
- O utilizador so consegue ver e editar as suas proprias tarefas.

## Testes rapidos

Apos arrancar o sistema, pode-se testar rapidamente com os seguintes comandos:

```bash
# 1. Registar um utilizador
curl -s -X POST http://localhost:5000/api/auth/registar \
  -H "Content-Type: application/json" \
  -d '{"nome": "Teste", "email": "teste@email.com", "senha": "123456"}' | python3 -m json.tool

# 2. Fazer login (guardar o token)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teste@email.com", "senha": "123456"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 3. Criar uma tarefa
curl -s -X POST http://localhost:5000/api/tarefas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"titulo": "Tarefa de teste", "descricao": "Testar o sistema", "data_limite": "2026-05-01"}' | python3 -m json.tool

# 4. Listar tarefas
curl -s http://localhost:5000/api/tarefas \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 5. Verificar estado do sistema
curl -s http://localhost:5000/api/saude | python3 -m json.tool
```
