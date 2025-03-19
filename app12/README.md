# App12 - Classificação de Feedbacks

Este projeto implementa um sistema fullstack para classificação de feedbacks em positivos ou negativos usando um modelo de classificação binária. O sistema permite que usuários enviem textos de feedback diretamente ou através de arquivos, e obtenham uma classificação do sentimento baseada no modelo treinado.

## Visão Geral

O projeto demonstra a integração entre:
- Um modelo de classificação binária (positivo/negativo) para análise de sentimentos
- API backend em FastAPI
- Frontend em React com upload de arquivos
- Banco de dados PostgreSQL
- Orquestração com Docker e docker-compose

## Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web rápido para construção de APIs
- **Scikit-learn**: Biblioteca de machine learning para modelo de classificação
- **NLTK**: Biblioteca para processamento de linguagem natural
- **SQLAlchemy**: ORM para interação com o banco de dados
- **PostgreSQL**: Banco de dados relacional para armazenar os feedbacks
- **Docker**: Containerização da aplicação

### Frontend
- **React**: Biblioteca JavaScript para construção de interfaces
- **Bootstrap/React-Bootstrap**: Framework CSS para design responsivo
- **Axios**: Cliente HTTP para requisições à API
- **React Icons**: Biblioteca de ícones
- **Docker**: Containerização da aplicação

## Estrutura do Projeto

```
app12/
├── backend/                 # API FastAPI e modelo ML
│   ├── main.py              # Aplicação principal FastAPI
│   ├── database.py          # Configuração do banco de dados
│   ├── train_model.py       # Script para treinar o modelo
│   ├── requirements.txt     # Dependências Python
│   └── Dockerfile           # Configuração do container do backend
├── frontend/                # Aplicação React
│   ├── src/                 # Código fonte React
│   │   ├── components/      # Componentes React
│   │   │   ├── FeedbackUploader.js  # Componente de upload
│   │   │   └── FeedbackHistory.js   # Componente de histórico
│   ├── public/              # Arquivos estáticos
│   ├── package.json         # Dependências do frontend
│   ├── nginx.conf           # Configuração do servidor nginx
│   └── Dockerfile           # Configuração do container do frontend
└── docker-compose.yml       # Orquestração dos serviços
```

## Funcionalidades Principais

1. **Upload de texto**: Os usuários podem inserir um texto de feedback diretamente em um formulário
2. **Upload de arquivo**: Os usuários podem enviar um arquivo texto (.txt) contendo o feedback
3. **Classificação em tempo real**: O sistema classifica o feedback como positivo ou negativo
4. **Visualização da confiança**: Exibe o nível de confiança da classificação
5. **Histórico de feedbacks**: Lista todos os feedbacks classificados anteriormente

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

1. **Processamento de Linguagem Natural (NLP)**: Utilização de técnicas de NLP para classificação de textos
2. **Upload de arquivos**: Implementação de upload de arquivos para processamento
3. **Machine Learning via API**: Exposição de modelo de ML através de uma API REST
4. **Persistência de dados**: Armazenamento de feedbacks e classificações em banco PostgreSQL
5. **Interface interativa**: Frontend com feedback visual da classificação
6. **Containerização**: Empacotamento da aplicação em contêineres Docker

## Modelo de Machine Learning

O modelo utilizado é um classificador binário baseado em:
- Vetorização TF-IDF para transformar texto em features numéricas
- Regressão Logística para classificação binária
- Pré-processamento de texto com NLTK

Para fins didáticos, o modelo é treinado com dados sintéticos gerados no início da aplicação, simulando feedbacks positivos e negativos em português. 