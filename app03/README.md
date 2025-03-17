# App 3 - API RESTful para Previsão de Preços de Imóveis

## Descrição
Este projeto implementa uma API RESTful completa utilizando FastAPI para o modelo de previsão de preços de imóveis. A API foi estruturada com documentação automática, validação de dados, tratamento de erros e endpoints bem definidos seguindo as melhores práticas RESTful.

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

Acesse a documentação interativa da API em `http://localhost:8000/docs`

### Endpoints disponíveis
- **GET /** - Informações gerais da API
- **POST /treinar/padrao** - Treina o modelo com dados pré-definidos
- **POST /treinar/personalizado** - Treina o modelo com dados personalizados
- **POST /prever** - Faz uma previsão do preço com base na área informada
- **GET /status** - Verifica o status do modelo
  
#### Exemplo de requisição para `/prever`:
```json
{
  "area": 120
}
```

#### Exemplo de requisição para `/treinar/personalizado`:
```json
{
  "X": [[50], [75], [100], [125], [150]],
  "y": [500000, 750000, 1000000, 1250000, 1500000]
}
```

## O que este projeto ensina
- Desenvolvimento de uma API RESTful completa com FastAPI
- Validação de dados com Pydantic
- Documentação automática de API (Swagger/OpenAPI)
- Tratamento estruturado de erros e exceções
- Design e versionamento adequados de endpoints
- Diferentes padrões de requisição e resposta
- Uso de tipos de dados fortemente tipados em Python
- Estruturação de uma API seguindo princípios RESTful 