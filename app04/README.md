# App 4 - API com Pré-processamento e Validação

## Descrição
Este projeto expande nosso modelo de previsão de preços de imóveis adicionando técnicas avançadas de pré-processamento de dados, validação de entrada e tratamento de dados faltantes. A API utiliza pipelines de processamento de dados do scikit-learn integrados ao modelo de machine learning.

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
- **POST /treinar** - Treina o modelo com dados customizáveis, incluindo múltiplas features
- **POST /prever** - Faz previsões com base em múltiplas características do imóvel
- **GET /status** - Verifica o status do modelo e features disponíveis
  
#### Exemplo de requisição para `/prever`:
```json
{
  "area": 120,
  "quartos": 3,
  "banheiros": 2,
  "idade_imovel": 5
}
```

#### Exemplo de requisição para `/treinar`:
```json
{
  "features": [
    {"area": 70, "quartos": 2, "banheiros": 1, "idade_imovel": 15},
    {"area": 100, "quartos": 3, "banheiros": 1, "idade_imovel": 10},
    {"area": 120, "quartos": 3, "banheiros": 2, "idade_imovel": 5},
    {"area": 150, "quartos": 4, "banheiros": 2, "idade_imovel": 3},
    {"area": 200, "quartos": 4, "banheiros": 3, "idade_imovel": 1}
  ],
  "precos": [600000, 850000, 1000000, 1250000, 1600000]
}
```

## O que este projeto ensina
- Técnicas de pré-processamento de dados usando scikit-learn:
  - Pipelines de transformação
  - Tratamento de valores ausentes (SimpleImputer)
  - Normalização/padronização de features (StandardScaler)
- Validação avançada de dados com Pydantic:
  - Validadores personalizados
  - Validação de tipos de dados
  - Validação de relacionamentos entre campos
- Tratamento de dados faltantes em APIs de machine learning
- Uso de dependências do FastAPI para pré-processamento
- Estruturação de um pipeline completo de ML (da validação à previsão)
- Cálculo e apresentação de faixas de confiança nas previsões 