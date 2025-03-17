# API de Previsão de Preços de Imóveis v8.0

Esta versão da API implementa uma arquitetura modularizada com design orientado a objetos e separação clara de responsabilidades. 

## Características

- **Estrutura modular** com separação das responsabilidades:
  - `api/`: Endpoints, middlewares e esquemas da API
  - `ml/`: Modelos e lógica de machine learning
  - `database/`: Configuração de banco de dados e modelos ORM
  - `utils/`: Funções auxiliares e utilitários

- **Orientação a objetos** para melhor organização do código:
  - Classe `ModeloPrecoImovel` para encapsular toda a lógica de ML
  - Classe `Logger` para gerenciamento de logs
  - Middlewares para autenticação e logging

- **Melhorias técnicas**:
  - Suporte a diferentes algoritmos de ML
  - Configuração de hiperparâmetros
  - Logging avançado com rotação de arquivos
  - Tratamento de erros consistente

## Estrutura do Projeto

```
app8/
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
├── main.py               # Ponto de entrada da aplicação
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

## Instalação

```bash
pip install -r requirements.txt
```

## Executando a Aplicação

```bash
cd app8
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

## O que este projeto ensina

Neste projeto, você aprenderá:

1. **Arquitetura modular** de aplicações Python:
   - Organização do código em módulos com responsabilidades específicas
   - Redução de acoplamento entre componentes

2. **Programação orientada a objetos** aplicada em APIs:
   - Encapsulamento de lógica em classes
   - Abstração de funcionalidades complexas

3. **Divisão de responsabilidades** em APIs de machine learning:
   - Separação de código de ML, API e persistência
   - Injeção de dependências entre componentes

4. **Boas práticas de desenvolvimento**:
   - Documentação eficiente de código
   - Tratamento de erros consistente
   - Logging estruturado
   - Configuração via variáveis de ambiente

5. **Design de APIs escaláveis**:
   - Middlewares para funcionalidades transversais
   - Autenticação com API key
   - Intercepção e formatação de erros

## Boas práticas implementadas

- **Separação de preocupações**: Cada módulo tem responsabilidades específicas
- **Princípio DRY** (Don't Repeat Yourself): Código reutilizável
- **Configuração externalizada**: Uso de variáveis de ambiente
- **Logging estruturado**: Rastreabilidade de operações
- **Tratamento de erros**: Respostas consistentes de erro
- **Versionamento de API**: Indicação clara da versão
- **Documentação completa**: Docstrings, README detalhado, OpenAPI

## Próximos passos sugeridos

- Implementar testes automatizados (unitários e de integração)
- Adicionar validação de dados mais sofisticada
- Implementar caching para melhorar performance
- Adicionar monitoramento de performance do modelo
- Implementar autenticação mais robusta (JWT/OAuth) 