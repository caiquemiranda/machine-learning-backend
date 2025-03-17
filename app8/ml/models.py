#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import joblib
import os
import json
from typing import Dict, List, Tuple, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import ModeloTreinamento, DadoTreinamento

class ModeloPrecoImovel:
    """
    Classe para gerenciar modelos de previsão de preços de imóveis.
    Suporta diferentes algoritmos de regressão e métricas de avaliação.
    """
    def __init__(self, logger):
        """
        Inicializa o modelo de previsão.
        
        Args:
            logger: Logger configurado para registrar atividades do modelo
        """
        self.logger = logger
        self.pipeline = None
        self.modelo_treinado = False
        self.metricas = {}
        self.feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
        self.modelos_disponiveis = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=0.1),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.modelo_dir = 'modelos'
        if not os.path.exists(self.modelo_dir):
            os.makedirs(self.modelo_dir)
        
    def _criar_pipeline(self, algoritmo='linear_regression', hiperparametros=None):
        """
        Cria um pipeline de pré-processamento e modelo.
        
        Args:
            algoritmo: Nome do algoritmo a ser usado
            hiperparametros: Dicionário com hiperparâmetros do modelo
        
        Returns:
            Pipeline configurado
        """
        numeric_features = self.feature_names
        
        # Preprocessamento para features numéricas
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])
        
        # Combinação de transformadores
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features)
            ],
            remainder='drop'
        )
        
        # Se hiperparâmetros foram fornecidos, configure o modelo
        modelo_base = self.modelos_disponiveis[algoritmo]
        if hiperparametros and algoritmo in hiperparametros:
            for param, valor in hiperparametros[algoritmo].items():
                if hasattr(modelo_base, param):
                    setattr(modelo_base, param, valor)
        
        # Criação do pipeline completo
        return Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', modelo_base)
        ])
    
    def treinar(self, X: np.ndarray, y: np.ndarray, 
                algoritmo: str = 'linear_regression', 
                hiperparametros: Optional[Dict] = None,
                db: Session = None) -> Dict[str, Any]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            X: Features para treinamento
            y: Targets (preços) para treinamento
            algoritmo: Nome do algoritmo a ser usado
            hiperparametros: Dicionário opcional com hiperparâmetros
            db: Sessão do banco de dados para persistência
            
        Returns:
            Dicionário com resultados do treinamento
        """
        request_id = str(uuid.uuid4())
        self.logger.info(f"Iniciando treinamento do modelo (ID: {request_id})")
        
        if algoritmo not in self.modelos_disponiveis:
            self.logger.error(f"Algoritmo {algoritmo} não suportado")
            raise ValueError(f"Algoritmo {algoritmo} não suportado. Opções: {list(self.modelos_disponiveis.keys())}")
        
        # Criar e treinar o pipeline
        self.pipeline = self._criar_pipeline(algoritmo, hiperparametros)
        self.pipeline.fit(X, y)
        self.modelo_treinado = True
        
        # Calcular métricas
        y_pred = self.pipeline.predict(X)
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)
        
        self.metricas = {
            'r2_score': r2,
            'rmse': rmse,
            'mae': mae
        }
        
        # Extrair coeficientes (se disponível)
        coeficientes = {}
        if hasattr(self.pipeline.named_steps['regressor'], 'coef_'):
            for i, feature in enumerate(self.feature_names):
                try:
                    coeficientes[feature] = float(self.pipeline.named_steps['regressor'].coef_[i])
                except (IndexError, TypeError):
                    pass
        
        if hasattr(self.pipeline.named_steps['regressor'], 'intercept_'):
            coeficientes['intercept'] = float(self.pipeline.named_steps['regressor'].intercept_)
            
        # Extrair informações sobre importância (para árvores)
        if hasattr(self.pipeline.named_steps['regressor'], 'feature_importances_'):
            for i, feature in enumerate(self.feature_names):
                try:
                    coeficientes[f"{feature}_importance"] = float(self.pipeline.named_steps['regressor'].feature_importances_[i])
                except (IndexError, TypeError):
                    pass
        
        resultados = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'algoritmo': algoritmo,
            'num_amostras': len(X),
            'r2_score': r2,
            'rmse': rmse,
            'mae': mae,
            'coeficientes': coeficientes,
            'features_utilizadas': self.feature_names,
            'hiperparametros': hiperparametros if hiperparametros else {}
        }
        
        # Salvar o modelo
        self.salvar_modelo()
        
        # Persistir informações no banco de dados (se fornecido)
        if db:
            self._persistir_treinamento(db, request_id, X, y, resultados)
            
        self.logger.info(f"Treinamento concluído. R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        return resultados
    
    def prever(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Realiza previsões usando o modelo treinado.
        
        Args:
            X: Features para previsão
            
        Returns:
            Tuple contendo previsões e intervalo de confiança
        """
        if not self.modelo_treinado:
            self.logger.error("Modelo não treinado. Treine o modelo antes de fazer previsões.")
            raise ValueError("Modelo não treinado. Treine o modelo antes de fazer previsões.")
        
        # Fazer previsão
        previsoes = self.pipeline.predict(X)
        
        # Estimar intervalo de confiança (simplificado)
        # Em um sistema real, isso dependeria do algoritmo usado
        erro_estimado = np.sqrt(self.metricas.get('rmse', 0.1))
        intervalo_confianca = np.array([
            previsoes - 2 * erro_estimado,  # limite inferior
            previsoes + 2 * erro_estimado   # limite superior
        ]).T
        
        return previsoes, intervalo_confianca
    
    def salvar_modelo(self, caminho: str = None) -> str:
        """
        Salva o modelo em disco.
        
        Args:
            caminho: Caminho onde salvar o modelo (opcional)
            
        Returns:
            Caminho onde o modelo foi salvo
        """
        if not self.modelo_treinado:
            self.logger.error("Não há modelo treinado para salvar")
            raise ValueError("Não há modelo treinado para salvar")
        
        if caminho is None:
            caminho = os.path.join(self.modelo_dir, 'modelo_pipeline.pkl')
            
        joblib.dump(self.pipeline, caminho)
        self.logger.info(f"Modelo salvo em {caminho}")
        
        # Salvar métricas separadamente para fácil acesso
        metricas_path = os.path.join(self.modelo_dir, 'metricas.json')
        with open(metricas_path, 'w') as f:
            json.dump(self.metricas, f)
            
        return caminho
    
    def carregar_modelo(self, caminho: str = None) -> bool:
        """
        Carrega um modelo salvo.
        
        Args:
            caminho: Caminho do modelo a ser carregado (opcional)
            
        Returns:
            True se o modelo foi carregado com sucesso
        """
        if caminho is None:
            caminho = os.path.join(self.modelo_dir, 'modelo_pipeline.pkl')
            
        if not os.path.exists(caminho):
            self.logger.warning(f"Arquivo de modelo não encontrado em {caminho}")
            return False
            
        try:
            self.pipeline = joblib.load(caminho)
            self.modelo_treinado = True
            
            # Carregar métricas se disponíveis
            metricas_path = os.path.join(self.modelo_dir, 'metricas.json')
            if os.path.exists(metricas_path):
                with open(metricas_path, 'r') as f:
                    self.metricas = json.load(f)
                    
            self.logger.info(f"Modelo carregado de {caminho}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo: {str(e)}")
            return False
    
    def _persistir_treinamento(self, db: Session, request_id: str, 
                              X: np.ndarray, y: np.ndarray, 
                              resultados: Dict[str, Any]):
        """
        Persiste os resultados do treinamento no banco de dados.
        
        Args:
            db: Sessão do banco de dados
            request_id: ID da requisição
            X: Features de treinamento
            y: Targets de treinamento
            resultados: Resultados do treinamento
        """
        try:
            # Criar registro do modelo
            modelo_db = ModeloTreinamento(
                request_id=request_id,
                timestamp=datetime.now(),
                num_amostras=resultados['num_amostras'],
                r2_score=resultados['r2_score'],
                rmse=resultados['rmse'],
                mae=resultados['mae'],
                coeficientes=resultados['coeficientes'],
                features_utilizadas=resultados['features_utilizadas'],
                algoritmo=resultados['algoritmo'],
                hiperparametros=resultados['hiperparametros'],
                ativo=True
            )
            
            db.add(modelo_db)
            db.flush()  # Para obter o ID do modelo
            
            # Adicionar dados de treinamento
            for i in range(len(X)):
                features = {}
                for j, nome in enumerate(self.feature_names):
                    if j < X.shape[1]:
                        features[nome] = X[i, j]
                
                dado = DadoTreinamento(
                    modelo_id=modelo_db.id,
                    area=features.get('area', None),
                    quartos=features.get('quartos', None),
                    banheiros=features.get('banheiros', None),
                    idade_imovel=features.get('idade_imovel', None),
                    preco=float(y[i])
                )
                db.add(dado)
            
            db.commit()
            self.logger.info(f"Treinamento persistido no banco de dados: ID={modelo_db.id}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Erro ao persistir treinamento: {str(e)}")
            raise 