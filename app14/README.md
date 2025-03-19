# Estimador de Tempo de Atendimento

Sistema de estimativa de tempo de atendimento baseado em machine learning, utilizando modelo de regressão para prever o tempo necessário para atender diferentes tipos de solicitações com base na complexidade.

## Funcionalidades

- Estimativa de tempo de atendimento com base em tipo de solicitação e complexidade
- Armazenamento de estimativas e tempo real para treinamento futuro
- Interface gráfica para visualização de histórico de estimativas
- Gerenciamento de tipos de solicitação
- Visualizações de dados por tipo de solicitação e complexidade
- Treinamento de modelos com dados históricos ou via upload de CSV

## Tecnologias Utilizadas

### Backend
- FastAPI (API REST)
- SQLAlchemy (ORM)
- PostgreSQL (Banco de Dados)
- Scikit-learn (Machine Learning)
- Pandas (Manipulação de dados)
- Matplotlib/Seaborn (Visualizações)

### Frontend
- React (Framework de UI)
- React Bootstrap (Componentes)
- React Router (Navegação)
- Axios (Requisições HTTP)
- Chart.js (Gráficos)

### DevOps
- Docker (Containerização)
- Docker Compose (Orquestração)

## Estrutura do Projeto

```
app14/
├── backend/
│   ├── models/             # Diretório onde os modelos ML são armazenados
│   ├── database.py         # Configuração do banco de dados e modelos ORM
│   ├── model.py            # Implementação do modelo de machine learning
│   ├── main.py             # API FastAPI
│   ├── Dockerfile          # Configuração para containerização do backend
│   └── requirements.txt    # Dependências do Python
├── frontend/
│   ├── public/             # Arquivos estáticos
│   ├── src/                # Código-fonte React
│   │   ├── components/     # Componentes React
│   │   ├── App.js          # Componente principal
│   │   └── index.js        # Ponto de entrada
│   ├── Dockerfile          # Configuração para containerização do frontend
│   ├── nginx.conf          # Configuração do Nginx para o frontend
│   └── package.json        # Dependências do Node.js
└── docker-compose.yml      # Configuração do Docker Compose
```

## Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados

### Passos
1. Clone o repositório:
   ```
   git clone <url-do-repositorio>
   cd machine-learning-backend/app14
   ```

2. Inicie os serviços com Docker Compose:
   ```
   docker-compose up -d
   ```

3. Acesse o sistema:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - Documentação da API: http://localhost:8000/docs

## Fluxo de Trabalho

1. Cadastre tipos de solicitação na aba "Tipos de Solicitação"
2. Faça estimativas na página inicial, fornecendo o tipo de solicitação e a complexidade
3. Opcionalmente, registre o tempo real de atendimento para melhorar o modelo
4. Visualize o histórico de estimativas na aba "Histórico"
5. Treine o modelo na aba "Informações do Modelo" após coletar dados suficientes
6. Visualize métricas e gráficos do modelo treinado

## Modelo de Machine Learning

O sistema utiliza um modelo de regressão (RandomForest ou LinearRegression) para estimar o tempo de atendimento com base em:
- Tipo de solicitação (categorizado usando OneHotEncoder)
- Complexidade (escala de 1 a 5)

As métricas de avaliação incluem:
- MSE (Erro Quadrático Médio)
- RMSE (Raiz do Erro Quadrático Médio)
- MAE (Erro Absoluto Médio)
- R² (Coeficiente de Determinação)

## Treinamento e Dados

O modelo pode ser treinado de duas formas:
1. Com dados registrados no sistema (estimativas com tempo real informado)
2. Via upload de arquivo CSV contendo as colunas:
   - tipo_solicitacao: Nome do tipo de solicitação
   - complexidade: Valor numérico de 1 a 5
   - tempo_atendimento: Tempo real em minutos 