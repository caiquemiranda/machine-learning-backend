# Sistema de Diagnóstico Preditivo com Machine Learning

Este projeto consiste em um sistema completo para diagnóstico preditivo utilizando técnicas de Machine Learning, composto por um backend em FastAPI/Python e um frontend em React.

## Visão Geral

O sistema permite realizar diagnósticos preditivos de saúde baseados em diversos parâmetros do paciente. Utilizando modelos de machine learning (Random Forest ou Regressão Logística), o sistema classifica os pacientes em diferentes níveis de risco: Saudável, Risco Baixo, Risco Moderado e Risco Alto.

### Principais Funcionalidades

- Dashboard com métricas e estatísticas do modelo atual
- Formulário para inserção de dados do paciente e obtenção de diagnóstico
- Histórico de diagnósticos realizados
- Interface para treinamento e configuração do modelo de ML
- Visualizações (matriz de confusão e importância de features)
- API RESTful para integração com outros sistemas

## Arquitetura

O projeto segue uma arquitetura de microserviços com três componentes principais:

1. **Backend (FastAPI/Python)**: API RESTful que gerencia modelos de ML, realiza predições e armazena dados.
2. **Frontend (React)**: Interface web responsiva para interação com o sistema.
3. **Banco de Dados (PostgreSQL)**: Armazena logs de predição, métricas de modelo e dados de treinamento.

## Requisitos

- Docker e Docker Compose
- Git

## Executando com Docker Compose

A maneira mais simples de executar o sistema é através do Docker Compose:

1. Clone o repositório:
   ```
   git clone <url-do-repositorio>
   cd github-machine-learning-backend/app13
   ```

2. Execute o Docker Compose:
   ```
   docker-compose up -d
   ```

3. Acesse a aplicação em:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Documentação da API: http://localhost:8000/docs

## Executando Manualmente

### Backend

1. Navegue até a pasta do backend:
   ```
   cd app13/backend
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure a variável de ambiente para o banco de dados:
   ```
   export DATABASE_URL="postgresql://usuario:senha@localhost:5432/diagnostic_system_db"
   ```

5. Execute o servidor:
   ```
   uvicorn main:app --reload
   ```

### Frontend

1. Navegue até a pasta do frontend:
   ```
   cd app13/frontend
   ```

2. Instale as dependências:
   ```
   npm install
   ```

3. Configure a URL do backend (opcional):
   ```
   echo "REACT_APP_API_URL=http://localhost:8000" > .env
   ```

4. Execute o servidor de desenvolvimento:
   ```
   npm start
   ```

## Estrutura do Projeto

```
app13/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py          # Ponto de entrada da API
│   ├── model.py         # Implementação dos modelos ML
│   └── database.py      # Configuração do banco de dados
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/  # Componentes React
│   │   ├── App.js       # Componente principal
│   │   └── api.js       # Cliente para comunicação com o backend
│   └── package.json
├── docker-compose.yml   # Configuração Docker Compose
└── README.md            # Este arquivo
```

## Endpoints da API

- `POST /predict`: Realiza um diagnóstico com base nos dados do paciente
- `POST /train`: Treina um novo modelo com configurações personalizadas
- `GET /metrics`: Retorna histórico de métricas dos modelos
- `GET /metrics/current`: Retorna métricas do modelo atual
- `GET /logs`: Retorna histórico de diagnósticos
- `GET /visualizations/confusion-matrix`: Retorna matriz de confusão como imagem
- `GET /visualizations/feature-importance`: Retorna gráfico de importância de features

## Desenvolvimento

Para contribuir com o projeto:

1. Crie um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Envie para o branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request 