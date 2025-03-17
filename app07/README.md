# API de Previsão de Preços de Imóveis v7.0

Esta versão da API inclui persistência com banco de dados SQLite para armazenar histórico de treinamentos, dados e previsões.

## Características

- Banco de dados SQLite para armazenamento persistente
- Modelos ORM para dados de treinamento, histórico de previsões e cadastro de modelos
- Endpoints avançados para consulta de histórico
- Suporte a múltiplos algoritmos de machine learning
- Validação de dados e tratamento de erros aprimorados
- Logging detalhado de operações
- Métricas de avaliação de modelos (R², RMSE, MAE)

## Estrutura do Projeto

```
app7/
├── database/             # Diretório para o arquivo do banco de dados SQLite
├── logs/                 # Logs da aplicação
├── modelos/              # Modelos de machine learning salvos
├── main.py               # Aplicação FastAPI principal
├── database.py           # Definições ORM e conexão com banco de dados
├── models.py             # Classes para gerenciamento de modelos de ML
└── requirements.txt      # Dependências do projeto
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

## Instalação

```bash
pip install -r requirements.txt
```

## Executando a Aplicação

```bash
cd app7
python main.py
```

A API estará disponível em: http://localhost:8000

## Documentação da API

A documentação interativa da API estará disponível em:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Endpoints Principais

- `GET /`: Informações sobre a API
- `POST /treinar`: Treina o modelo com dados fornecidos
- `POST /prever`: Realiza previsões com o modelo treinado
- `GET /status`: Retorna o status atual do modelo e estatísticas
- `GET /previsoes`: Lista histórico de previsões feitas
- `GET /treinamentos`: Lista histórico de treinamentos realizados
- `GET /treinamentos/{id}`: Detalhes de um treinamento específico

## Exemplos de Uso

### Treinamento do Modelo

```bash
curl -X POST "http://localhost:8000/treinar" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [
      {"area": 100, "quartos": 2, "banheiros": 1, "idade_imovel": 10},
      {"area": 150, "quartos": 3, "banheiros": 2, "idade_imovel": 5},
      {"area": 200, "quartos": 4, "banheiros": 3, "idade_imovel": 2}
    ],
    "precos": [300000, 450000, 650000]
  }'
```

### Realizar uma Previsão

```bash
curl -X POST "http://localhost:8000/prever" \
  -H "Content-Type: application/json" \
  -d '{
    "area": 120,
    "quartos": 2,
    "banheiros": 1,
    "idade_imovel": 8
  }'
```

### Verificar Status

```bash
curl -X GET "http://localhost:8000/status"
```

### Visualizar Histórico de Previsões

```bash
curl -X GET "http://localhost:8000/previsoes?limit=10&offset=0"
```

## Banco de Dados

A aplicação utiliza SQLAlchemy com SQLite para persistência. O banco de dados armazena:

1. **Modelos de Treinamento**: Histórico de todos os treinamentos realizados, incluindo métricas e coeficientes
2. **Dados de Treinamento**: Todos os dados utilizados para treinar os modelos
3. **Previsões**: Histórico de todas as previsões realizadas

## Segurança

Esta versão é destinada a desenvolvimento. Para ambientes de produção, considere:

- Implementar autenticação e autorização
- Usar um banco de dados mais robusto (PostgreSQL/MySQL)
- Configurar HTTPS
- Adicionar rate limiting 