import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
from typing import Dict, Any, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para salvar modelos
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Versão atual do modelo
CURRENT_VERSION = "1.0.0"

class MLModel:
    """Classe genérica para modelos de machine learning."""
    
    def __init__(self, model_type: str = "classifier", model_name: str = "default"):
        """
        Inicializa o modelo de ML.
        
        Args:
            model_type: Tipo de modelo ('classifier' ou 'regressor')
            model_name: Nome do modelo
        """
        self.model_type = model_type
        self.model_name = model_name
        self.model = None
        self.pipeline = None
        self.label_encoders = {}
        self.feature_names = []
        self.target_name = ""
        self.is_trained = False
        self.metrics = {}
        self.version = CURRENT_VERSION
    
    def preprocess_data(self, X: pd.DataFrame, y: Optional[pd.Series] = None, training: bool = False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Pré-processa os dados para treinamento ou previsão.
        
        Args:
            X: DataFrame com features
            y: Series com target (opcional)
            training: Se é fase de treinamento
            
        Returns:
            X_processed: Features processadas
            y_processed: Target processado (se disponível)
        """
        if training:
            # Na fase de treinamento, salvar os nomes das features
            self.feature_names = list(X.columns)
            if y is not None:
                self.target_name = y.name if hasattr(y, 'name') else 'target'
            
            # Criar pipeline de pré-processamento
            self.pipeline = Pipeline([
                ('scaler', StandardScaler())
            ])
            
            # Ajustar o pipeline aos dados
            X_processed = self.pipeline.fit_transform(X)
            
            # Para classificação, codificar o target
            if y is not None and self.model_type == "classifier":
                self.label_encoders['target'] = LabelEncoder()
                y_processed = self.label_encoders['target'].fit_transform(y)
            else:
                y_processed = y
                
        else:
            # Na fase de predição, usar o pipeline já treinado
            if self.pipeline is None:
                raise ValueError("O pipeline não foi treinado. Treine o modelo primeiro.")
                
            X_processed = self.pipeline.transform(X)
            y_processed = None
        
        return X_processed, y_processed
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            X: DataFrame com features
            y: Series com target
            
        Returns:
            metrics: Métricas de desempenho do modelo
        """
        logger.info(f"Treinando modelo {self.model_type} {self.model_name}")
        
        # Pré-processar dados
        X_processed, y_processed = self.preprocess_data(X, y, training=True)
        
        # Criar modelo
        if self.model_type == "classifier":
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif self.model_type == "regressor":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Tipo de modelo desconhecido: {self.model_type}")
        
        # Treinar modelo
        self.model.fit(X_processed, y_processed)
        self.is_trained = True
        
        # Calcular métricas
        y_pred = self.model.predict(X_processed)
        
        if self.model_type == "classifier":
            self.metrics = {
                'accuracy': accuracy_score(y_processed, y_pred),
                'report': classification_report(y_processed, y_pred, output_dict=True)
            }
        else:  # regressor
            self.metrics = {
                'mse': mean_squared_error(y_processed, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_processed, y_pred)),
                'r2': r2_score(y_processed, y_pred)
            }
        
        logger.info(f"Modelo treinado. Métricas: {self.metrics}")
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Faz previsões com o modelo treinado.
        
        Args:
            X: DataFrame com features
            
        Returns:
            predictions: Array com previsões
        """
        if not self.is_trained:
            raise ValueError("O modelo não foi treinado. Treine o modelo primeiro.")
        
        # Pré-processar dados
        X_processed, _ = self.preprocess_data(X, training=False)
        
        # Fazer previsões
        predictions = self.model.predict(X_processed)
        
        # Para classificação, converter códigos para rótulos originais
        if self.model_type == "classifier" and 'target' in self.label_encoders:
            predictions = self.label_encoders['target'].inverse_transform(predictions)
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Faz previsões de probabilidade para classificação.
        
        Args:
            X: DataFrame com features
            
        Returns:
            probabilities: Array com probabilidades
        """
        if not self.is_trained:
            raise ValueError("O modelo não foi treinado. Treine o modelo primeiro.")
        
        if self.model_type != "classifier":
            raise ValueError("Previsão de probabilidade disponível apenas para classificação.")
        
        # Pré-processar dados
        X_processed, _ = self.preprocess_data(X, training=False)
        
        # Fazer previsões de probabilidade
        probabilities = self.model.predict_proba(X_processed)
        
        return probabilities
    
    def save(self, filepath: Optional[str] = None) -> str:
        """
        Salva o modelo treinado.
        
        Args:
            filepath: Caminho para salvar o modelo (opcional)
            
        Returns:
            saved_path: Caminho onde o modelo foi salvo
        """
        if not self.is_trained:
            raise ValueError("O modelo não foi treinado. Treine o modelo primeiro.")
        
        if filepath is None:
            # Nome baseado no tipo e timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.model_type}_{self.model_name}_{timestamp}.joblib"
            filepath = os.path.join(MODEL_DIR, filename)
        
        # Dados a serem salvos
        model_data = {
            'model': self.model,
            'pipeline': self.pipeline,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'model_type': self.model_type,
            'model_name': self.model_name,
            'is_trained': self.is_trained,
            'metrics': self.metrics,
            'version': self.version
        }
        
        # Salvar modelo
        joblib.dump(model_data, filepath)
        logger.info(f"Modelo salvo em {filepath}")
        
        return filepath
    
    def load(self, filepath: str) -> None:
        """
        Carrega um modelo salvo.
        
        Args:
            filepath: Caminho do arquivo do modelo
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        # Carregar modelo
        model_data = joblib.load(filepath)
        
        # Atualizar atributos
        self.model = model_data['model']
        self.pipeline = model_data['pipeline']
        self.label_encoders = model_data['label_encoders']
        self.feature_names = model_data['feature_names']
        self.target_name = model_data['target_name']
        self.model_type = model_data['model_type']
        self.model_name = model_data['model_name']
        self.is_trained = model_data['is_trained']
        self.metrics = model_data['metrics']
        self.version = model_data.get('version', "1.0.0")
        
        logger.info(f"Modelo carregado de {filepath}")
    
    def feature_importance(self) -> Dict[str, float]:
        """
        Obtém a importância das features do modelo.
        
        Returns:
            importance: Dicionário com importância das features
        """
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            raise ValueError("Modelo não treinado ou não suporta importância de features.")
        
        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        return importance
    
    def generate_visualizations(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, str]:
        """
        Gera visualizações para o modelo.
        
        Args:
            X: DataFrame com features
            y: Series com target
            
        Returns:
            paths: Dicionário com caminhos das visualizações
        """
        # Criar diretório para visualizações
        viz_dir = os.path.join(MODEL_DIR, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        paths = {}
        
        # Visualização de importância de features
        if self.is_trained and hasattr(self.model, 'feature_importances_'):
            plt.figure(figsize=(10, 6))
            importance = self.feature_importance()
            sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            features, values = zip(*sorted_imp)
            
            sns.barplot(x=list(values), y=list(features))
            plt.title('Importância das Features')
            plt.tight_layout()
            
            filepath = os.path.join(viz_dir, f"{self.model_type}_{self.model_name}_feature_importance.png")
            plt.savefig(filepath)
            plt.close()
            
            paths['feature_importance'] = filepath
            
        # Visualizações específicas por tipo de modelo
        if self.model_type == "classifier" and self.is_trained:
            # Matriz de confusão para classificação
            if y is not None:
                X_processed, y_processed = self.preprocess_data(X, y, training=False)
                y_pred = self.model.predict(X_processed)
                
                plt.figure(figsize=(8, 6))
                conf_matrix = pd.crosstab(
                    y_processed, y_pred, 
                    rownames=['Real'], 
                    colnames=['Predito']
                )
                sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues')
                plt.title('Matriz de Confusão')
                
                filepath = os.path.join(viz_dir, f"{self.model_type}_{self.model_name}_confusion_matrix.png")
                plt.savefig(filepath)
                plt.close()
                
                paths['confusion_matrix'] = filepath
                
        elif self.model_type == "regressor" and self.is_trained:
            # Gráfico de valores reais vs. preditos para regressão
            if y is not None:
                X_processed, y_processed = self.preprocess_data(X, y, training=False)
                y_pred = self.model.predict(X_processed)
                
                plt.figure(figsize=(8, 8))
                plt.scatter(y_processed, y_pred, alpha=0.5)
                plt.plot([y_processed.min(), y_processed.max()], [y_processed.min(), y_processed.max()], 'k--')
                plt.xlabel('Valores Reais')
                plt.ylabel('Valores Preditos')
                plt.title('Regressão: Real vs. Predito')
                
                filepath = os.path.join(viz_dir, f"{self.model_type}_{self.model_name}_real_vs_predicted.png")
                plt.savefig(filepath)
                plt.close()
                
                paths['real_vs_predicted'] = filepath
                
                # Histograma de erros
                errors = y_processed - y_pred
                plt.figure(figsize=(10, 6))
                sns.histplot(errors, kde=True)
                plt.xlabel('Erro de Predição')
                plt.ylabel('Frequência')
                plt.title('Distribuição dos Erros de Predição')
                
                filepath = os.path.join(viz_dir, f"{self.model_type}_{self.model_name}_error_distribution.png")
                plt.savefig(filepath)
                plt.close()
                
                paths['error_distribution'] = filepath
        
        return paths


# Função utilitária para carregar o modelo padrão
def get_model(model_type: str = "classifier", model_name: str = "default") -> MLModel:
    """
    Obtém um modelo - carrega se existir, ou cria um novo.
    
    Args:
        model_type: Tipo de modelo ('classifier' ou 'regressor')
        model_name: Nome do modelo
    
    Returns:
        model: Instância do modelo
    """
    model = MLModel(model_type=model_type, model_name=model_name)
    
    # Verificar se existe um modelo salvo
    model_files = [f for f in os.listdir(MODEL_DIR) if f.startswith(f"{model_type}_{model_name}") and f.endswith(".joblib")]
    
    if model_files:
        # Carregar o modelo mais recente (ordenado por nome)
        latest_model = sorted(model_files)[-1]
        model_path = os.path.join(MODEL_DIR, latest_model)
        model.load(model_path)
    
    return model 