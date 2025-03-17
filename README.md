# Série de Projetos de Backend com Machine Learning

Este repositório contém uma série de 10 projetos progressivos que demonstram a evolução de uma aplicação backend com foco em Machine Learning. Cada projeto adiciona novas funcionalidades e conceitos, permitindo um aprendizado gradual e estruturado de técnicas avançadas de integração de ML com sistemas backend.

## Progressão dos Projetos

### App 1: API Básica de Previsão de Preços
- API simples usando Flask
- Modelo básico de Regressão Linear
- Endpoints para treinar e fazer previsões
- Primeiro contato com integração de ML em API web

### App 2: Refatoração e Melhorias Básicas
- Migração para FastAPI para melhor desempenho e documentação
- Estruturação do código em módulos
- Validação de dados de entrada com Pydantic
- Serialização/desserialização de JSON
- Documentação automática com Swagger/OpenAPI

### App 3: Persistência e Gestão de Modelos
- Salvamento e carregamento de modelos treinados
- Versionamento de modelos
- Gestão de diferentes algoritmos de ML
- Métricas de avaliação de modelos
- Visualização básica de dados

### App 4: Persistência de Dados
- Integração com SQLite via SQLAlchemy
- Armazenamento de histórico de previsões
- Modelos ORM para dados e metadados
- Consultas e filtragem de dados históricos
- Rastreamento de uso do modelo

### App 5: Logging, Tratamento de Erros e Testes
- Sistema robusto de logging
- Tratamento avançado de erros
- Testes unitários para API e modelos
- Monitoramento básico da aplicação
- Rastreamento de requisições

### App 6: API Completa com Autenticação
- Sistema de autenticação e autorização
- Diferentes níveis de acesso
- Proteção de endpoints
- Gestão de usuários e permissões
- Configuração avançada da aplicação

### App 7: Performance e Escalabilidade
- Otimização de desempenho
- Implementação de cache
- Processamento em background
- Paginação e filtragem avançada
- Limitação de taxa de requisições

### App 8: Features Avançadas de ML
- Múltiplos algoritmos de ML
- Hiperparâmetros configuráveis
- Validação cruzada
- Feature engineering
- Geração de visualizações mais complexas

### App 9: Processamento Assíncrono
- Tarefas assíncronas com Celery e Redis
- Filas de processamento para tarefas de ML
- Status e rastreamento de tarefas
- Escalabilidade horizontal
- APIs assíncronas

### App 10: Containerização e CI/CD
- Dockerização completa
- Orquestração com Docker Compose
- Pipeline CI/CD com GitHub Actions e Jenkins
- Monitoramento com Prometheus e Sentry
- Configurações para diferentes ambientes
- Deploy automatizado

## Tecnologias Utilizadas na Progressão

| Tecnologia | Aplicações |
|------------|------------|
| **Frameworks Web** | Flask (App1), FastAPI (App2-10) |
| **Machine Learning** | scikit-learn, pandas, numpy |
| **Banco de Dados** | SQLite (App4-8), PostgreSQL (App9-10) |
| **Processamento Assíncrono** | Celery, Redis (App9-10) |
| **Frontend/UI** | Swagger/ReDoc, Matplotlib/Plotly para visualizações |
| **Deploy/DevOps** | Docker, Docker Compose, GitHub Actions, Jenkins |
| **Monitoramento** | Prometheus, Sentry, Logging customizado |
| **Autenticação** | JWT, OAuth (App6-10) |

## Como Utilizar os Projetos

Cada pasta (`app1`, `app2`, etc.) contém um projeto completo e independente, com seu próprio README que explica:
- Funcionalidades específicas
- Instruções de instalação
- Como executar o projeto
- Endpoints disponíveis
- Conceitos de ML e backend ensinados

Recomendamos seguir a progressão numérica para um aprendizado gradual, mas cada projeto pode ser usado individualmente.

## Requisitos Globais

- Python 3.7+
- Conhecimentos básicos de:
  - Programação Python
  - Conceitos de APIs REST
  - Fundamentos de Machine Learning

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues para reportar bugs ou sugerir melhorias. Pull requests são apreciados.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
