# API de Previsão de Preços de Imóveis v9.0

Esta versão da API implementa processamento assíncrono com Celery e Redis para tarefas de treinamento e previsão, permitindo melhor escalabilidade e desempenho.

## Características

- **Processamento assíncrono** para tarefas demoradas:
  - Treinamento de modelos em background
  - Previsões em lote sem bloquear a API
  - Monitoramento de status de tarefas

- **Integração com Celery e Redis**:
  - Filas de tarefas distribuídas
  - Workers independentes para processamento
  - Persistência de resultados

- **Melhorias técnicas**:
  - Configuração centralizada com Pydantic
  - Monitoramento de tarefas com Flower
  - Rastreamento de tarefas no banco de dados
  - Endpoints para consulta de status

## Estrutura do Projeto

```
app9/
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
│   ├── helper.py         # Funções auxiliares
│   └── logger.py         # Configuração de logs
├── logs/                 # Diretório para logs
├── modelos/              # Diretório para modelos salvos
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

## Instalação

```bash
pip install -r requirements.txt
```

## Executando a Aplicação

### 1. Iniciar o Redis (necessário para o Celery)

```bash
# Usando Docker (recomendado)
docker run -d -p 6379:6379 redis

# Ou instale e execute o Redis localmente conforme documentação
```

### 2. Iniciar o Worker Celery

```bash
cd app9
celery -A worker worker --loglevel=info
```

### 3. Iniciar o Flower (opcional, para monitoramento)

```bash
cd app9
celery -A worker flower
```

### 4. Iniciar a API

```bash
cd app9
python main.py
```

A API estará disponível em: http://localhost:8000
O Flower estará disponível em: http://localhost:5555

## Documentação da API

A documentação interativa da API estará disponível em:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Endpoints Principais

- `GET /`: Informações sobre a API
- `POST /treinar`: Treina o modelo com dados fornecidos (síncrono ou assíncrono)
- `POST /prever`: Realiza previsões com o modelo treinado (síncrono ou assíncrono)
- `GET /tarefa/{task_id}`: Verifica o status de uma tarefa assíncrona
- `GET /tarefas`: Lista todas as tarefas assíncronas
- `GET /status`: Retorna o status atual do modelo e estatísticas
- `GET /celery-status`: Verifica o status do Celery e seus workers

## O que este projeto ensina

Neste projeto, você aprenderá:

1. **Processamento assíncrono** em aplicações de machine learning:
   - Separação de tarefas demoradas do fluxo principal da API
   - Implementação de filas de tarefas com Celery
   - Monitoramento e rastreamento de tarefas

2. **Integração com sistemas de mensageria**:
   - Configuração do Redis como broker de mensagens
   - Comunicação entre API e workers
   - Persistência de resultados de tarefas

3. **Arquitetura escalável**:
   - Distribuição de carga entre múltiplos workers
   - Processamento paralelo de tarefas
   - Resiliência a falhas

4. **Boas práticas de desenvolvimento**:
   - Configuração centralizada com Pydantic e variáveis de ambiente
   - Monitoramento de tarefas com Flower
   - Rastreamento de estado no banco de dados

## Boas práticas implementadas

- **Processamento assíncrono**: Tarefas demoradas não bloqueiam a API
- **Monitoramento de tarefas**: Rastreamento completo do ciclo de vida
- **Configuração centralizada**: Uso de Pydantic para validação e carregamento
- **Escalabilidade horizontal**: Possibilidade de adicionar mais workers
- **Resiliência**: Recuperação de falhas e persistência de estado

## Próximos passos sugeridos

- Implementar autenticação JWT para endpoints
- Adicionar suporte a filas prioritárias
- Implementar retry automático para tarefas falhas
- Adicionar testes automatizados para tarefas assíncronas
- Implementar cache de resultados para previsões frequentes 