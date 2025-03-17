# App 1 - API Básica de Previsão de Preços de Imóveis

## Descrição
Este é um projeto simples que demonstra a integração de um modelo de machine learning com uma API web. Implementamos um modelo de regressão linear que prevê o preço de um imóvel com base em sua área.

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
   pip install flask numpy scikit-learn joblib
   ```

### Executando a aplicação
```
python main.py
```

A API estará disponível em `http://localhost:5000`

### Endpoints disponíveis
- **GET /** - Página inicial da API
- **GET /treinar** - Treina o modelo com dados de exemplo
- **POST /prever** - Faz uma previsão do preço com base na área informada
  
Exemplo de requisição para `/prever`:
```json
{
  "area": 120
}
```

## O que este projeto ensina
- Conceitos básicos de machine learning usando scikit-learn
- Como criar um modelo de regressão linear simples
- Como integrar um modelo de ML com uma API web usando Flask
- Como estruturar endpoints RESTful básicos
- Receber e processar dados de requisições HTTP 