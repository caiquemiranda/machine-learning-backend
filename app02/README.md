# App 2 - API de Previsão de Preços de Imóveis com Persistência

## Descrição
Este projeto aprimora o App 1, adicionando persistência de dados ao modelo de machine learning. Agora, o modelo treinado é salvo em disco e pode ser carregado novamente quando a aplicação for reiniciada.

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

A API estará disponível em `http://localhost:5000`

### Endpoints disponíveis
- **GET /** - Página inicial da API
- **GET /treinar** - Treina o modelo com dados de exemplo e salva em disco
- **POST /prever** - Faz uma previsão do preço com base na área informada
- **GET /status** - Verifica o status do modelo (se está salvo e carregado)
  
Exemplo de requisição para `/prever`:
```json
{
  "area": 120
}
```

## O que este projeto ensina
- Como persistir modelos de machine learning em disco usando joblib
- Técnicas para carregar automaticamente modelos pré-treinados
- Gerenciamento de estados em uma API de machine learning
- Verificação do status do modelo
- Estruturação de um projeto básico de ML com persistência de dados 