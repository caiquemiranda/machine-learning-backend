# App 5 - API com Logging, Tratamento de Erros e Testes

## Descrição
Este projeto expande nossa API de previsão de preços de imóveis adicionando um sistema robusto de logging, manipulação avançada de erros e testes unitários. A aplicação agora registra todas as operações, fornece mensagens de erro detalhadas e inclui uma suíte completa de testes para garantir seu funcionamento correto.

## Como Executar

### Pré-requisitos
- Python 3.7+
- pip (gerenciador de pacotes do Python)

### Instalação
1. Clone este repositório
2. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows:
   ```
   venv\Scripts\activate
   ```
   - Linux/MacOS:
   ```
   source venv/bin/activate
   ```
4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

### Executando a aplicação
```
python main.py
```

A API estará disponível em `http://localhost:8000`

### Executando os testes
```
python -m unittest test_api.py
```

### Endpoints disponíveis
- **GET /** - Informações gerais da API
- **POST /treinar** - Treina o modelo com dados customizáveis
- **POST /prever** - Faz previsões com base nas características do imóvel
- **GET /status** - Verifica o status do modelo e estatísticas da API
- **POST /admin/limpar-logs** - Limpa os logs (apenas para desenvolvimento)

## Recursos Implementados

### Sistema de Logging
- Log de todas as requisições com IDs únicos para rastreamento
- Registro de tempos de resposta, erros e performance do modelo
- Logs persistidos em arquivo para análise posterior
- Diferentes níveis de log (INFO, WARNING, ERROR, DEBUG)

### Tratamento Avançado de Erros
- Middleware para captura de exceções não tratadas
- Manipuladores personalizados para erros HTTP e validação
- Formatação consistente de mensagens de erro
- Inclusão de IDs de requisição em todas as respostas de erro

### Testes Unitários
- Testes para todos os endpoints principais
- Verificação de validação de entrada
- Testes de fluxo completo (treinar → prever)
- Testes de casos de erro

### Monitoramento
- Estatísticas da API em tempo real (requisições, sucessos, falhas)
- Tempo de atividade (uptime)
- Contadores de operações (previsões e treinamentos)
- Registro do último erro

## O que este projeto ensina
- Implementação de logging em aplicações Python
- Padrões de tratamento de erros em APIs RESTful
- Uso de middleware no FastAPI
- Desenvolvimento orientado a testes (TDD) em APIs de ML
- Rastreamento de requisições em sistemas distribuídos
- Monitoramento básico de aplicações
- Princípios de design para alta observabilidade 