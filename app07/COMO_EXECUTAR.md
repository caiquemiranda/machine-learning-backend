# Como Executar a Aplicação

Este guia explica como configurar e executar tanto a API de previsão de preços de imóveis quanto a interface web.

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- Acesso à linha de comando/terminal

## Instalação

1. Clone o repositório ou baixe os arquivos da aplicação
2. Navegue até a pasta do projeto:

```bash
cd caminho/para/app7
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

Este comando instalará todas as bibliotecas necessárias, incluindo FastAPI, SQLAlchemy, Streamlit, e suas dependências.

## Executando a API

Para iniciar o servidor da API, execute:

```bash
python main.py
```

Isso iniciará a API na porta 8000. Você deverá ver uma saída semelhante a:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

A API agora está em execução e pronta para receber requisições.

### Acessando a Documentação da API

A documentação interativa da API estará disponível em:

- [http://localhost:8000/docs](http://localhost:8000/docs) - Interface Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) - Interface ReDoc

Estas páginas permitem explorar e testar todos os endpoints disponíveis.

## Executando a Interface Web

Com a API em execução, abra um novo terminal e navegue até a pasta do projeto:

```bash
cd caminho/para/app7
```

Para iniciar a interface web com Streamlit, execute:

```bash
streamlit run web_app.py
```

Isso iniciará o servidor da interface web e abrirá automaticamente seu navegador no endereço padrão (geralmente http://localhost:8501).

Se o navegador não abrir automaticamente, basta acessar o URL mostrado no terminal.

## Utilizando a Aplicação

### Fluxo de Uso Básico

1. Na interface web, vá para a aba "Treinar" e treine o modelo usando os dados de exemplo ou fornecendo seus próprios dados
2. Após o treinamento bem-sucedido, vá para a aba "Prever" para fazer previsões de preços com base nas características do imóvel
3. Explore o histórico de previsões e treinamentos na aba "Histórico"

### Testando a API Diretamente

Você também pode interagir diretamente com a API usando ferramentas como cURL, Postman, ou a documentação interativa Swagger:

**Exemplo de treinamento (cURL):**

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

**Exemplo de previsão (cURL):**

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

## Solução de Problemas

### Porta já em Uso

Se receber um erro indicando que a porta já está em uso:

- Para a API: Modifique a porta no arquivo `main.py`, na linha `uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)`
- Para o Streamlit: Execute com uma porta específica: `streamlit run web_app.py --server.port=8502`

### Erro de Conexão com a API

Se a interface web não conseguir se conectar à API:

1. Verifique se a API está em execução
2. Confirme que a URL base está correta em `web_app.py` (por padrão, `API_URL = "http://localhost:8000"`)
3. Verifique se algum firewall ou antivírus está bloqueando a conexão

### Erro no Banco de Dados

Se ocorrerem erros relacionados ao banco de dados:

1. Verifique se a pasta `database` foi criada
2. Em caso de problemas persistentes, exclua o arquivo `database/imoveis.db` e reinicie a API para recriar o banco de dados

## Encerrando a Aplicação

Para encerrar a aplicação:

1. Pressione `Ctrl+C` no terminal onde a API está em execução
2. Pressione `Ctrl+C` no terminal onde a interface web está em execução 