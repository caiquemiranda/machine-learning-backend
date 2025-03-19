# Sistema Multi-usuário de Previsões com JWT

Um sistema completo de previsões com machine learning que utiliza autenticação JWT para usuários. O sistema permite que múltiplos usuários registrem-se, façam login e realizem previsões usando modelos de machine learning.

## Funcionalidades

- **Autenticação**
  - Registro de usuários com validação
  - Login com JWT (JSON Web Tokens)
  - Perfis de usuários
  - Administração de usuários

- **Previsões com Machine Learning**
  - Modelos de classificação
  - Modelos de regressão
  - Histórico de previsões por usuário
  - Treinamento de modelos

- **Interface de Usuário**
  - Dashboard com estatísticas
  - Formulários para previsões
  - Visualização de histórico
  - Perfil de usuário

## Tecnologias Utilizadas

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Scikit-learn
- Pandas
- JWT Authentication (python-jose)
- Passlib (com bcrypt)

### Frontend
- React
- React Bootstrap
- React Router
- Axios
- JWT Decode
- Formik & Yup

### DevOps
- Docker
- Docker Compose
- Nginx

## Estrutura do Projeto

```
app15/
├── backend/
│   ├── auth.py - Autenticação JWT
│   ├── database.py - Modelos ORM e conexão com banco de dados
│   ├── main.py - API principal
│   ├── model.py - Modelos de machine learning
│   ├── requirements.txt - Dependências
│   └── Dockerfile
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/ - Componentes React
│   │   ├── contexts/ - Contextos React (autenticação)
│   │   ├── pages/ - Páginas da aplicação
│   │   ├── services/ - Serviços de API
│   │   ├── App.js - Componente principal
│   │   └── index.js - Ponto de entrada
│   ├── package.json
│   ├── nginx.conf - Configuração do Nginx
│   └── Dockerfile
│
├── docker-compose.yml - Orquestração de serviços
└── README.md - Este arquivo
```

## Instruções de Execução

### Pré-requisitos
- Docker
- Docker Compose

### Passos

1. Clone o repositório
```
git clone [url-do-repositorio]
cd app15
```

2. Inicie os serviços com Docker Compose
```
docker-compose up --build
```

3. Acesse a aplicação
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs

4. Credenciais padrão de admin
   - Usuário: admin
   - Senha: admin123

## Fluxo de Uso

1. **Registro e Login**
   - Registre um novo usuário
   - Faça login para obter o token JWT

2. **Dashboard**
   - Visualize estatísticas e previsões recentes

3. **Fazer uma Previsão**
   - Selecione classificação ou regressão
   - Preencha os valores das features
   - Visualize o resultado da previsão

4. **Histórico**
   - Visualize todas as previsões feitas
   - Ordene e filtre resultados

5. **Perfil**
   - Atualize suas informações
   - Altere sua senha

## Detalhes da API

A API inclui endpoints para:

- Autenticação (`/api/token`, `/api/users`)
- Previsões (`/api/predictions`)
- Modelos (`/api/models/*`)
- Usuário atual (`/api/users/me`)
- Estatísticas (`/api/stats`)
- Logs (`/api/logs`)
- Administração (`/api/admin/*`) - requer privilégios de admin

Para mais detalhes, acesse a documentação do Swagger em http://localhost:8000/docs

## Segurança

- Senhas armazenadas com hash usando bcrypt
- Autenticação via JWT com expiração de tokens
- Proteção de rotas por tipo de usuário
- Validação de dados em todos os endpoints
- Logs de atividades do usuário 