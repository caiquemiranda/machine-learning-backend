import os
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Union, Optional, Any

from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from ..config import Config

# Configuração do logger
logger = logging.getLogger(__name__)

class ModeloPrecoImovel:
    """
    Classe para treinamento e previsão de preços de imóveis com suporte para processamento assíncrono.
    """
    
    # Dicionário de algoritmos suportados
    ALGORITMOS = {
        "linear_regression": LinearRegression,
        "ridge": Ridge,
        "lasso": Lasso,
        "elastic_net": ElasticNet,
        "random_forest": RandomForestRegressor,
        "gradient_boosting": GradientBoostingRegressor,
        "svr": SVR
    }
    
    # Hiperparâmetros padrão para cada algoritmo
    HIPERPARAMETROS_PADRAO = {
        "linear_regression": {},
        "ridge": {"alpha": 1.0},
        "lasso": {"alpha": 1.0},
        "elastic_net": {"alpha": 1.0, "l1_ratio": 0.5},
        "random_forest": {"n_estimators": 100, "max_depth": 10},
        "gradient_boosting": {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
        "svr": {"kernel": "rbf", "C": 1.0, "epsilon": 0.1}
    }
    
    def __init__(self):
        """
        Inicializa o modelo de previsão de preços de imóveis.
        """
        self.modelo = None
        self.scaler = StandardScaler()
        self.algoritmo = None
        self.features = None
        self.data_treinamento = None
        self.metricas = {}
        
        # Criar diretório para modelos se não existir
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
        
        # Tentar carregar um modelo existente
        self.carregar_modelo()
    
    def carregar_modelo(self, caminho_modelo: str = None) -> bool:
        """
        Carrega um modelo salvo anteriormente.
        
        Args:
            caminho_modelo: Caminho para o arquivo do modelo. Se None, usa o padrão.
            
        Returns:
            bool: True se o modelo foi carregado com sucesso, False caso contrário.
        """
        if caminho_modelo is None:
            caminho_modelo = os.path.join(Config.MODELS_DIR, Config.MODEL_FILE)
        
        try:
            if os.path.exists(caminho_modelo):
                modelo_dict = joblib.load(caminho_modelo)
                self.modelo = modelo_dict.get("modelo")
                self.scaler = modelo_dict.get("scaler")
                self.algoritmo = modelo_dict.get("algoritmo")
                self.features = modelo_dict.get("features")
                self.data_treinamento = modelo_dict.get("data_treinamento")
                self.metricas = modelo_dict.get("metricas", {})
                
                logger.info(f"Modelo carregado com sucesso: {self.algoritmo}")
                return True
            else:
                logger.warning(f"Arquivo de modelo não encontrado: {caminho_modelo}")
                return False
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            return False
    
    def salvar_modelo(self, caminho_modelo: str = None) -> bool:
        """
        Salva o modelo treinado em um arquivo.
        
        Args:
            caminho_modelo: Caminho para salvar o arquivo do modelo. Se None, usa o padrão.
            
        Returns:
            bool: True se o modelo foi salvo com sucesso, False caso contrário.
        """
        if self.modelo is None:
            logger.warning("Não há modelo para salvar")
            return False
        
        if caminho_modelo is None:
            caminho_modelo = os.path.join(Config.MODELS_DIR, Config.MODEL_FILE)
        
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(caminho_modelo), exist_ok=True)
            
            # Salvar modelo e metadados
            modelo_dict = {
                "modelo": self.modelo,
                "scaler": self.scaler,
                "algoritmo": self.algoritmo,
                "features": self.features,
                "data_treinamento": self.data_treinamento,
                "metricas": self.metricas
            }
            
            joblib.dump(modelo_dict, caminho_modelo)
            logger.info(f"Modelo salvo com sucesso: {caminho_modelo}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {str(e)}")
            return False
    
    def _preparar_dados(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara os dados para treinamento ou previsão.
        
        Args:
            df: DataFrame com os dados
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Features e target (se disponível)
        """
        # Verificar se o DataFrame está vazio
        if df.empty:
            raise ValueError("DataFrame vazio")
        
        # Verificar colunas necessárias
        colunas_necessarias = ['area', 'quartos', 'banheiros', 'idade_imovel']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                raise ValueError(f"Coluna obrigatória ausente: {coluna}")
        
        # Separar features e target (se disponível)
        X = df[colunas_necessarias].copy()
        y = df['preco'].values if 'preco' in df.columns else None
        
        # Armazenar nomes das features
        self.features = colunas_necessarias
        
        return X, y
    
    def treinar(self, df: pd.DataFrame, algoritmo: str = "linear_regression", 
                hiperparametros: Dict = None, test_size: float = 0.2, 
                random_state: int = 42) -> Dict[str, float]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            df: DataFrame com os dados de treinamento
            algoritmo: Nome do algoritmo a ser utilizado
            hiperparametros: Hiperparâmetros para o algoritmo
            test_size: Proporção do conjunto de teste
            random_state: Semente aleatória
            
        Returns:
            Dict[str, float]: Métricas de desempenho do modelo
        """
        logger.info(f"Iniciando treinamento com algoritmo: {algoritmo}")
        
        # Verificar se o algoritmo é suportado
        if algoritmo not in self.ALGORITMOS:
            algoritmos_disponiveis = ", ".join(self.ALGORITMOS.keys())
            raise ValueError(f"Algoritmo não suportado: {algoritmo}. Disponíveis: {algoritmos_disponiveis}")
        
        # Usar hiperparâmetros padrão se não fornecidos
        if hiperparametros is None:
            hiperparametros = self.HIPERPARAMETROS_PADRAO[algoritmo]
        
        # Preparar dados
        X, y = self._preparar_dados(df)
        
        if y is None:
            raise ValueError("Coluna 'preco' não encontrada nos dados de treinamento")
        
        # Dividir em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Instanciar e treinar o modelo
        self.algoritmo = algoritmo
        self.modelo = self.ALGORITMOS[algoritmo](**hiperparametros)
        self.modelo.fit(X_train_scaled, y_train)
        self.data_treinamento = datetime.now()
        
        # Avaliar o modelo
        y_pred = self.modelo.predict(X_test_scaled)
        
        # Calcular métricas
        self.metricas = {
            "r2_score": r2_score(y_test, y_pred),
            "mae": mean_absolute_error(y_test, y_pred),
            "mse": mean_squared_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "tamanho_dataset": len(df),
            "tamanho_treino": len(X_train),
            "tamanho_teste": len(X_test)
        }
        
        logger.info(f"Treinamento concluído. R²: {self.metricas['r2_score']:.4f}, RMSE: {self.metricas['rmse']:.2f}")
        
        return self.metricas
    
    def prever(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza uma previsão para um único imóvel.
        
        Args:
            dados: Dicionário com características do imóvel
            
        Returns:
            Dict[str, Any]: Resultado da previsão
        """
        if self.modelo is None:
            raise ValueError("Modelo não treinado. Execute treinar() primeiro.")
        
        # Converter dicionário para DataFrame
        df = pd.DataFrame([dados])
        
        # Garantir que todas as features necessárias estão presentes
        for feature in self.features:
            if feature not in df.columns:
                df[feature] = 0  # Valor padrão
        
        # Selecionar apenas as features utilizadas no treinamento
        X = df[self.features]
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        # Fazer previsão
        valor_previsto = float(self.modelo.predict(X_scaled)[0])
        
        # Calcular intervalo de confiança (simplificado)
        # Em um caso real, seria mais complexo e dependeria do algoritmo
        margem_erro = 0.1 * valor_previsto  # 10% de margem
        intervalo_min = valor_previsto - margem_erro
        intervalo_max = valor_previsto + margem_erro
        
        # Montar resultado
        resultado = {
            "valor_previsto": valor_previsto,
            "intervalo_confianca": {
                "min": intervalo_min,
                "max": intervalo_max
            },
            "algoritmo": self.algoritmo,
            "timestamp": datetime.now().isoformat()
        }
        
        return resultado
    
    def prever_lote(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Realiza previsões para múltiplos imóveis.
        
        Args:
            df: DataFrame com características dos imóveis
            
        Returns:
            List[Dict[str, Any]]: Lista de resultados de previsão
        """
        if self.modelo is None:
            raise ValueError("Modelo não treinado. Execute treinar() primeiro.")
        
        resultados = []
        
        # Garantir que todas as features necessárias estão presentes
        for feature in self.features:
            if feature not in df.columns:
                df[feature] = 0  # Valor padrão
        
        # Selecionar apenas as features utilizadas no treinamento
        X = df[self.features]
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        # Fazer previsões
        previsoes = self.modelo.predict(X_scaled)
        
        # Processar cada previsão
        for i, valor_previsto in enumerate(previsoes):
            # Calcular intervalo de confiança (simplificado)
            margem_erro = 0.1 * valor_previsto  # 10% de margem
            intervalo_min = valor_previsto - margem_erro
            intervalo_max = valor_previsto + margem_erro
            
            # Montar resultado
            resultado = {
                "id": i,
                "valor_previsto": float(valor_previsto),
                "intervalo_confianca": {
                    "min": float(intervalo_min),
                    "max": float(intervalo_max)
                }
            }
            
            # Adicionar dados originais se disponíveis
            if not df.empty:
                for feature in self.features:
                    if feature in df.columns:
                        resultado[feature] = float(df.iloc[i][feature])
            
            resultados.append(resultado)
        
        return resultados
    
    def obter_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo atual.
        
        Returns:
            Dict[str, Any]: Informações do modelo
        """
        return {
            "modelo_treinado": self.modelo is not None,
            "algoritmo": self.algoritmo,
            "features": self.features,
            "data_treinamento": self.data_treinamento.isoformat() if self.data_treinamento else None,
            "metricas": self.metricas,
            "total_previsoes": 0  # Em uma implementação real, seria obtido do banco de dados
        }
 