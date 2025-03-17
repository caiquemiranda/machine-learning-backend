# API de Previsão de Preços de Imóveis v10.0

Esta versão da API implementa uma arquitetura completa com Docker, orquestração e CI/CD, preparando o sistema para produção em grande escala.

## Características

- **Arquitetura containerizada**:
  - Aplicação completa em contêineres Docker
  - Orquestração com Docker Compose
  - Configurações específicas para ambientes de desenvolvimento, staging e produção

- **Integração e Entrega Contínua (CI/CD)**:
  - Pipeline automatizado com GitHub Actions ou Jenkins
  - Testes automatizados
  - Análise estática de código
  - Deploy automatizado para ambientes de staging e produção

- **Monitoramento e observabilidade**:
  - Métricas com Prometheus
  - Logging centralizado em formato JSON
  - Rastreamento de erros com Sentry
  - Monitoramento de tarefas assíncronas

- **Banco de dados PostgreSQL**:
  - Persistência de dados em banco relacional
  - Migrations e versionamento de esquema
  - Volumes persistentes para dados

- **Processamento assíncrono**:
  - Tarefas de ML em background com Celery
  - Redis como broker de mensagens
  - Monitoramento de tarefas com Flower

## Estrutura do Projeto

```
app10/
├── api/                  # Módulo da API
│   ├── __init__.py      
│   ├── endpoints.py      # Endpoints da API
│   ├── middleware.py     # Middlewares (logging, auth)
│   └── schemas.py        # Esquemas Pydantic
├── database/             # Módulo de banco de dados
│   ├── __init__.py
│   ├── database.py       # Conexão com BD
│   └── models.py         # Modelos ORM
├── ml/                   # Módulo de machine learning
│   ├── __init__.py
│   └── models.py         # Classe de ML
├── utils/                # Utilitários
│   ├── __init__.py
│   ├── metrics.py        # Métricas Prometheus
│   └── logger.py         # Configuração de logs
├── tests/                # Testes automatizados
│   ├── __init__.py
│   ├── test_api.py       # Testes da API
│   └── test_ml.py        # Testes de ML
├── ci/                   # Configurações de CI/CD
│   ├── Jenkinsfile       # Pipeline Jenkins
│   └── github-actions-ci.yml # Pipeline GitHub Actions
├── logs/                 # Diretório para logs
├── modelos/              # Diretório para modelos salvos
├── Dockerfile            # Dockerfile para API
├── Dockerfile.worker     # Dockerfile para worker Celery
├── docker-compose.yml    # Configuração Docker Compose base
├── docker-compose.prod.yml # Configuração para produção
├── docker-compose.staging.yml # Configuração para staging
├── .env.example          # Exemplo de variáveis de ambiente
├── config.py             # Configurações centralizadas
├── main.py               # Ponto de entrada da aplicação
├── worker.py             # Worker Celery para processamento assíncrono
└── requirements.txt      # Dependências
```

## Dependências

O projeto requer as seguintes bibliotecas:

- fastapi
- uvicorn
- pydantic
- sqlalchemy
- psycopg2-binary
- numpy
- scikit-learn
- joblib
- pandas
- matplotlib
- seaborn
- plotly
- python-multipart
- python-dotenv
- celery
- redis
- flower
- httpx
- pytest
- prometheus-client
- sentry-sdk
- python-json-logger
- gunicorn

## Instalação e Execução

### Usando Docker (Recomendado)

1. **Configuração de ambiente**

   Copie o arquivo de exemplo de variáveis de ambiente e ajuste conforme necessário:

   ```bash
   cp .env.example .env
   ```

2. **Iniciar a aplicação com Docker Compose**

   ```bash
   # Ambiente de desenvolvimento
   docker-compose up -d

   # Ambiente de staging
   docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

   # Ambiente de produção
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Verificar logs**

   ```bash
   docker-compose logs -f
   ```

### Instalação Manual (Desenvolvimento)

1. **Criar ambiente virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Instalar dependências**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente**

   ```bash
   cp .env.example .env
   # Edite o arquivo .env conforme necessário
   ```

4. **Iniciar serviços necessários (Redis e PostgreSQL)**

   ```bash
   # Usando Docker para os serviços
   docker-compose up -d redis db
   ```

5. **Iniciar a API**

   ```bash
   python -m app10.main
   ```

6. **Iniciar o worker Celery**

   ```bash
   celery -A app10.worker worker --loglevel=info
   ```

7. **Iniciar o Flower (opcional, para monitoramento)**

   ```bash
   celery -A app10.worker flower
   ```

## Acessando a API

A API estará disponível em:

- **API**: http://localhost:8000
- **Documentação Swagger**: http://localhost:8000/docs
- **Documentação ReDoc**: http://localhost:8000/redoc
- **Monitoramento Flower**: http://localhost:5555

## Endpoints Principais

- `GET /`: Informações sobre a API
- `POST /prever`: Realiza previsões com o modelo treinado (síncrono ou assíncrono)
- `POST /treinar`: Treina o modelo com dados fornecidos (síncrono ou assíncrono)
- `GET /tarefa/{task_id}`: Verifica o status de uma tarefa assíncrona
- `GET /tarefas`: Lista todas as tarefas assíncronas
- `GET /status`: Retorna o status atual do modelo e estatísticas
- `GET /celery-status`: Verifica o status do Celery e seus workers
- `GET /health`: Endpoint para health check
- `GET /metrics`: Métricas Prometheus

## CI/CD

O projeto inclui configurações para integração contínua e entrega contínua usando:

1. **GitHub Actions**: Arquivo de configuração em `.github/workflows/ci.yml`
2. **Jenkins**: Arquivo de configuração em `ci/Jenkinsfile`

O pipeline de CI/CD inclui:

- Verificação de qualidade de código (linting)
- Execução de testes automatizados
- Construção de imagens Docker
- Deploy para ambientes de staging e produção

## O que este projeto ensina

Neste projeto, você aprenderá:

1. **Containerização e orquestração**:
   - Criação de imagens Docker para aplicações Python
   - Configuração de serviços com Docker Compose
   - Estratégias de deployment para diferentes ambientes

2. **CI/CD e DevOps**:
   - Configuração de pipelines de integração contínua
   - Automação de testes e deployment
   - Práticas de DevOps para aplicações de ML

3. **Arquitetura escalável para ML**:
   - Separação de API e workers para processamento assíncrono
   - Estratégias de escalabilidade horizontal
   - Gerenciamento de recursos em contêineres

4. **Monitoramento e observabilidade**:
   - Implementação de métricas com Prometheus
   - Logging estruturado em formato JSON
   - Rastreamento de erros com Sentry

5. **Boas práticas de desenvolvimento**:
   - Configuração centralizada com Pydantic
   - Testes automatizados
   - Documentação de API com OpenAPI

## Próximos passos sugeridos

- Implementar Kubernetes para orquestração em larga escala
- Adicionar autenticação OAuth2/JWT
- Implementar cache distribuído com Redis
- Adicionar balanceamento de carga com Nginx
- Implementar backup automatizado de dados
- Configurar alertas baseados em métricas 