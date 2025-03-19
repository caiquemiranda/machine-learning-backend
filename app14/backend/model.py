import pandas as pd
import numpy as np
import joblib
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para salvar modelos
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

class EstimadorTempoAtendimento:
    """Modelo para estimar o tempo de atendimento com base no tipo de solicitação e complexidade."""
    
    def __init__(self, model_type: str = "linear_regression"):
        """
        Inicializa o modelo de estimativa de tempo de atendimento.
        
        Args:
            model_type: Tipo de modelo a ser usado (linear_regression ou random_forest)
        """
        self.model_type = model_type
        self.model = None
        self.preprocessor = None
        self.is_trained = False
        self.features = ['tipo_solicitacao', 'complexidade']
        self.target = 'tempo_atendimento'
        
        # Mapeamento de tipos de solicitação para uso no modelo
        self.tipo_solicitacao_mapping = {}
        
        # Métricas do modelo
        self.metrics = {}
    
    def _preprocess_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocessa os dados para treinamento ou previsão.
        
        Args:
            data: DataFrame com os dados de entrada
        
        Returns:
            X: Dados de features processados
            y: Valores alvo (se disponíveis, senão None)
        """
        # Verificar se os dados contêm as colunas necessárias
        for feature in self.features:
            if feature not in data.columns:
                raise ValueError(f"Feature '{feature}' não encontrada nos dados")
        
        # Separar features e target (se disponível)
        X = data[self.features].copy()
        y = data[self.target] if self.target in data.columns else None
        
        # Criar preprocessador se ele ainda não existir
        if self.preprocessor is None:
            categorical_features = ['tipo_solicitacao']
            numeric_features = ['complexidade']
            
            categorical_transformer = Pipeline(steps=[
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])
            
            numeric_transformer = Pipeline(steps=[
                ('scaler', StandardScaler())
            ])
            
            self.preprocessor = ColumnTransformer(
                transformers=[
                    ('cat', categorical_transformer, categorical_features),
                    ('num', numeric_transformer, numeric_features)
                ]
            )
            
            # Se estamos treinando, ajustamos o preprocessador aos dados
            if y is not None:
                self.preprocessor.fit(X)
        
        # Transformar os dados
        X_processed = self.preprocessor.transform(X)
        
        return X_processed, y
    
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            data: DataFrame com os dados de treinamento
        
        Returns:
            metrics: Dicionário com métricas de desempenho do modelo
        """
        logger.info(f"Treinando modelo {self.model_type} com {len(data)} amostras")
        
        # Atualizar o mapeamento de tipos de solicitação
        self.tipo_solicitacao_mapping = {
            value: idx for idx, value in enumerate(data['tipo_solicitacao'].unique())
        }
        
        # Preprocessar dados
        X, y = self._preprocess_data(data)
        
        if y is None:
            raise ValueError("Dados de treinamento não contêm a coluna alvo 'tempo_atendimento'")
        
        # Criar e treinar o modelo
        if self.model_type == "linear_regression":
            self.model = LinearRegression()
        elif self.model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Tipo de modelo desconhecido: {self.model_type}")
        
        # Treinar o modelo
        self.model.fit(X, y)
        self.is_trained = True
        
        # Calcular métricas no conjunto de treinamento
        y_pred = self.model.predict(X)
        self.metrics = {
            'mse': mean_squared_error(y, y_pred),
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred)
        }
        
        logger.info(f"Modelo treinado. Métricas: {self.metrics}")
        
        return self.metrics
    
    def predict(self, tipo_solicitacao: str, complexidade: int) -> float:
        """
        Faz uma previsão de tempo de atendimento com base no tipo de solicitação e complexidade.
        
        Args:
            tipo_solicitacao: Nome do tipo de solicitação
            complexidade: Nível de complexidade (1-5)
        
        Returns:
            tempo_estimado: Tempo estimado em minutos
        """
        if not self.is_trained:
            raise ValueError("O modelo não foi treinado ainda. Treine o modelo antes de fazer previsões.")
        
        # Criar DataFrame com os dados de entrada
        data = pd.DataFrame({
            'tipo_solicitacao': [tipo_solicitacao],
            'complexidade': [complexidade]
        })
        
        # Preprocessar dados
        X, _ = self._preprocess_data(data)
        
        # Fazer previsão
        tempo_estimado = self.model.predict(X)[0]
        
        # Garantir que o tempo estimado não seja negativo
        tempo_estimado = max(0, tempo_estimado)
        
        return float(tempo_estimado)
    
    def save_model(self, filename: str = None) -> str:
        """
        Salva o modelo treinado em um arquivo.
        
        Args:
            filename: Nome do arquivo (opcional)
        
        Returns:
            path: Caminho do arquivo salvo
        """
        if not self.is_trained:
            raise ValueError("O modelo não foi treinado ainda. Treine o modelo antes de salvar.")
        
        if filename is None:
            filename = f"tempo_atendimento_{self.model_type}.joblib"
        
        model_path = os.path.join(MODEL_DIR, filename)
        
        model_data = {
            'model': self.model,
            'preprocessor': self.preprocessor,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'features': self.features,
            'target': self.target,
            'tipo_solicitacao_mapping': self.tipo_solicitacao_mapping,
            'metrics': self.metrics
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"Modelo salvo em {model_path}")
        
        return model_path
    
    def load_model(self, filename: str = None) -> None:
        """
        Carrega um modelo treinado de um arquivo.
        
        Args:
            filename: Nome do arquivo (opcional)
        """
        if filename is None:
            filename = f"tempo_atendimento_{self.model_type}.joblib"
        
        model_path = os.path.join(MODEL_DIR, filename)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {model_path}")
        
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.preprocessor = model_data['preprocessor']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        self.features = model_data['features']
        self.target = model_data['target']
        self.tipo_solicitacao_mapping = model_data['tipo_solicitacao_mapping']
        self.metrics = model_data['metrics']
        
        logger.info(f"Modelo carregado de {model_path}")
    
    def generate_visualization(self, data: pd.DataFrame, save_path: str = None) -> Dict[str, str]:
        """
        Gera visualizações para análise do modelo.
        
        Args:
            data: DataFrame com os dados para visualização
            save_path: Caminho para salvar as imagens (opcional)
        
        Returns:
            paths: Dicionário com caminhos das imagens geradas
        """
        if save_path is None:
            save_path = os.path.join(MODEL_DIR, "visualizations")
        
        os.makedirs(save_path, exist_ok=True)
        
        image_paths = {}
        
        # Histograma de tempo de atendimento
        plt.figure(figsize=(10, 6))
        sns.histplot(data[self.target], kde=True)
        plt.title('Distribuição de Tempo de Atendimento')
        plt.xlabel('Tempo (minutos)')
        plt.ylabel('Frequência')
        hist_path = os.path.join(save_path, 'tempo_distribuicao.png')
        plt.savefig(hist_path)
        plt.close()
        image_paths['histogram'] = hist_path
        
        # Tempo de atendimento por tipo de solicitação
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='tipo_solicitacao', y=self.target, data=data)
        plt.title('Tempo de Atendimento por Tipo de Solicitação')
        plt.xlabel('Tipo de Solicitação')
        plt.ylabel('Tempo (minutos)')
        plt.xticks(rotation=45)
        boxplot_path = os.path.join(save_path, 'tempo_por_tipo.png')
        plt.savefig(boxplot_path)
        plt.close()
        image_paths['boxplot'] = boxplot_path
        
        # Tempo de atendimento por complexidade
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='complexidade', y=self.target, data=data)
        plt.title('Tempo de Atendimento por Nível de Complexidade')
        plt.xlabel('Complexidade')
        plt.ylabel('Tempo (minutos)')
        complexity_path = os.path.join(save_path, 'tempo_por_complexidade.png')
        plt.savefig(complexity_path)
        plt.close()
        image_paths['complexity'] = complexity_path
        
        return image_paths 