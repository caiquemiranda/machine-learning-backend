# App11 - Previsão de Preço de Casas

Este projeto implementa um sistema fullstack para previsão de preço de casas usando um modelo de regressão linear. O sistema permite que usuários informem características da casa (área, número de quartos, banheiros, etc.) e obtenham uma estimativa de preço baseada no modelo treinado.

## Visão Geral

O projeto demonstra a integração entre:
- Um modelo de machine learning simples (regressão linear)
- API backend em FastAPI
- Frontend em React
- Banco de dados PostgreSQL
- Orquestração com Docker e docker-compose

## Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web rápido para construção de APIs
- **Scikit-learn**: Biblioteca de machine learning para modelo de regressão linear
- **SQLAlchemy**: ORM para interação com o banco de dados
- **PostgreSQL**: Banco de dados relacional para armazenar as previsões
- **Docker**: Containerização da aplicação

### Frontend
- **React**: Biblioteca JavaScript para construção de interfaces
- **Bootstrap/React-Bootstrap**: Framework CSS para design responsivo
- **Axios**: Cliente HTTP para requisições à API
- **Docker**: Containerização da aplicação

## Estrutura do Projeto

```
app11/
├── backend/                 # API FastAPI e modelo ML
│   ├── main.py              # Aplicação principal FastAPI
│   ├── database.py          # Configuração do banco de dados
│   ├── train_model.py       # Script para treinar o modelo
│   ├── requirements.txt     # Dependências Python
│   └── Dockerfile           # Configuração do container do backend
├── frontend/                # Aplicação React
│   ├── src/                 # Código fonte React
│   ├── public/              # Arquivos estáticos
│   ├── package.json         # Dependências do frontend
│   ├── nginx.conf           # Configuração do servidor nginx
│   └── Dockerfile           # Configuração do container do frontend
└── docker-compose.yml       # Orquestração dos serviços
```

## Como Executar o Projeto

### Pré-requisitos
- Docker e docker-compose instalados na sua máquina

### Passos para Execução

1. Clone o repositório e navegue até a pasta do projeto

2. Inicie os contêineres com docker-compose:
   ```bash
   docker-compose up -d
   ```

3. Acesse a aplicação:
   - Frontend: http://localhost:3000
   - API Swagger: http://localhost:8000/docs

4. Para interromper a execução:
   ```bash
   docker-compose down
   ```

## O que você vai aprender com este projeto

Este projeto demonstra a integração completa de um sistema fullstack com machine learning, incluindo:

1. **Integração backend-frontend**: Comunicação entre React e FastAPI via requisições HTTP
2. **Implementação de API**: Criação de endpoints REST para previsão e listagem de dados
3. **Machine Learning via API**: Exposição de modelo de ML através de uma API REST
4. **Persistência de dados**: Armazenamento de previsões em banco PostgreSQL
5. **Containerização**: Empacotamento da aplicação em contêineres Docker
6. **Orquestração de serviços**: Gerenciamento de múltiplos serviços com docker-compose

## Modelo de Machine Learning

O modelo utilizado é uma regressão linear simples que estima preços de casas com base nas seguintes características:
- Área (m²)
- Número de quartos
- Número de banheiros
- Número de andares
- Vagas de estacionamento
- Idade da casa

Para fins didáticos, o modelo é treinado com dados sintéticos gerados no início da aplicação. 