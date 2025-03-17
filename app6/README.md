# App 6 - API com Dashboard para Visualização de Métricas

## Descrição
Este projeto expande nossa API de previsão de preços de imóveis adicionando um dashboard interativo com Streamlit para visualização de métricas, análises e histórico de previsões. O sistema agora mantém um histórico persistente das previsões realizadas e oferece visualizações detalhadas do comportamento do modelo.

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
1. Inicie a API:
   ```
   python main.py
   ```
   A API estará disponível em `http://localhost:8000`

2. Em outra janela de terminal (mantendo a API rodando), inicie o dashboard:
   ```
   streamlit run dashboard.py
   ```
   O dashboard estará disponível em `http://localhost:8501`

## Componentes do Sistema

### API RESTful
- Endpoints para treinamento do modelo, previsões e consulta de status
- Histórico persistente de previsões
- Sistema completo de logging e tratamento de erros
- Métricas e estatísticas da API

### Dashboard Interativo
- Painel de controle com métricas da API e status do modelo
- Ferramenta para realizar novas previsões
- Visualizações:
  - Distribuição dos preços previstos
  - Correlações entre características e preços
  - Histórico de previsões ao longo do tempo
  - Tabela de dados detalhados
- Filtros interativos e atualização automática

## Funcionalidades do Dashboard
- **Estatísticas da API**: Uptime, requisições, previsões e treinamentos realizados
- **Previsão Rápida**: Interface para testar o modelo em tempo real
- **Análises Visuais**: Histogramas, boxplots, scatter plots e gráficos de linha
- **Matriz de Correlação**: Visualização das relações entre as diferentes características
- **Histórico Temporal**: Acompanhe as previsões ao longo do tempo
- **Filtros Interativos**: Explore os dados com filtros dinâmicos

## O que este projeto ensina
- Desenvolvimento de dashboards interativos com Streamlit
- Visualização de dados em tempo real
- Integração entre API backend e frontend de visualização
- Persistência de histórico de previsões
- Análise exploratória de dados de machine learning
- Design de interfaces intuitivas para usuários finais
- Implementação de métricas e KPIs para modelos de ML 