#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import logging
import joblib
from typing import Dict, List, Tuple, Any, Optional, Union
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Configuração de logging
logger = logging.getLogger('imoveis-api.models')

# Diretório para modelos
MODEL_DIR = 'modelos'
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Nomes das features
FEATURE_NAMES = ['area', 'quartos', 'banheiros', 'idade_imovel']

class ModeloPrecoImovel:
    """
    Classe para gerenciar modelos de previsão de preços de imóveis.
    Encapsula diferentes algoritmos de machine learning e funcionalidades
    como treinamento, avaliação e previsão.
    """
    
    def __init__(self, tipo_modelo='linear', caminho_modelo=None):
        """
        Inicializa o modelo de previsão.
        
        Args:
            tipo_modelo (str): Tipo de modelo a ser utilizado 
                               ('linear', 'ridge', 'lasso', 'elastic_net', 'rf', 'gb')
            caminho_modelo (str): Caminho para carregar um modelo já treinado
        """
        self.tipo_modelo = tipo_modelo
        self.pipeline = None
        self.caminho_modelo = caminho_modelo or os.path.join(MODEL_DIR, f'modelo_{tipo_modelo}.pkl')
        self.estatisticas = {
            'mse': None,
            'rmse': None,
            'mae': None,
            'r2': None,
            'num_amostras': 0,
            'coeficientes': {},
            'importancia_features': {},
            'cross_val_scores': []
        }
        
        # Tenta carregar o modelo existente ou cria um novo
        self._carregar_ou_criar_modelo()
    
    def _carregar_ou_criar_modelo(self):
        """
        Carrega um modelo existente ou cria um novo pipeline.
        """
        if os.path.exists(self.caminho_modelo):
            try:
                logger.info(f"Carregando modelo de {self.caminho_modelo}")
                self.pipeline = joblib.load(self.caminho_modelo)
                logger.info("Modelo carregado com sucesso")
                return True
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}")
        
        logger.info(f"Criando novo pipeline com modelo {self.tipo_modelo}")
        self.pipeline = self._criar_pipeline()
        return False
    
    def _criar_pipeline(self):
        """
        Cria um pipeline de pré-processamento e modelo.
        
        Returns:
            Pipeline: Pipeline scikit-learn configurado
        """
        # Preprocessador numérico
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # Define as colunas
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, FEATURE_NAMES)
            ]
        )
        
        # Seleciona o algoritmo conforme o tipo especificado
        if self.tipo_modelo == 'ridge':
            regressor = Ridge(alpha=1.0)
        elif self.tipo_modelo == 'lasso':
            regressor = Lasso(alpha=0.1)
        elif self.tipo_modelo == 'elastic_net':
            regressor = ElasticNet(alpha=0.1, l1_ratio=0.5)
        elif self.tipo_modelo == 'rf':
            regressor = RandomForestRegressor(
                n_estimators=100, 
                max_depth=None, 
                min_samples_split=2,
                random_state=42
            )
        elif self.tipo_modelo == 'gb':
            regressor = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
        else:  # linear por padrão
            regressor = LinearRegression()
        
        # Monta o pipeline completo
        return Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', regressor)
        ])
    
    def treinar(self, X: np.ndarray, y: np.ndarray, validacao: bool = True, 
                test_size: float = 0.2, cv: int = 5) -> Dict[str, Any]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            X: Matriz de features
            y: Vetor alvo (preços)
            validacao: Se deve realizar validação com dados de teste
            test_size: Proporção de dados para teste
            cv: Número de folds para validação cruzada
            
        Returns:
            Dict com estatísticas do treinamento
        """
        logger.info(f"Iniciando treinamento com {len(X)} amostras")
        
        # Atualiza contador de amostras
        self.estatisticas['num_amostras'] = len(X)
        
        # Divide os dados em treino e teste se necessário
        if validacao:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Treina com os dados de treino
            self.pipeline.fit(X_train, y_train)
            
            # Avalia com os dados de teste
            self._calcular_metricas(X_test, y_test)
            
            # Validação cruzada para robustez
            scores = cross_val_score(
                self.pipeline, X, y, cv=cv, scoring='neg_mean_squared_error'
            )
            self.estatisticas['cross_val_scores'] = [-score for score in scores]
            
            logger.info(f"Validação cruzada MSE: {np.mean(self.estatisticas['cross_val_scores']):.4f} ± {np.std(self.estatisticas['cross_val_scores']):.4f}")
        else:
            # Treina com todos os dados
            self.pipeline.fit(X, y)
            
            # Calcula métricas no conjunto de treino (pode ter overfitting)
            self._calcular_metricas(X, y)
        
        # Armazena importância/coeficientes das features
        self._extrair_importancia_features()
        
        # Salva o modelo treinado
        self._salvar_modelo()
        
        return self.estatisticas
    
    def _calcular_metricas(self, X: np.ndarray, y: np.ndarray):
        """
        Calcula métricas de avaliação do modelo.
        
        Args:
            X: Matriz de features
            y: Vetor alvo (preços)
        """
        # Faz previsões
        y_pred = self.pipeline.predict(X)
        
        # Calcula métricas
        self.estatisticas['mse'] = mean_squared_error(y, y_pred)
        self.estatisticas['rmse'] = np.sqrt(self.estatisticas['mse'])
        self.estatisticas['mae'] = mean_absolute_error(y, y_pred)
        self.estatisticas['r2'] = r2_score(y, y_pred)
        
        logger.info(f"Métricas de avaliação: R²={self.estatisticas['r2']:.4f}, "
                   f"RMSE={self.estatisticas['rmse']:.2f}, "
                   f"MAE={self.estatisticas['mae']:.2f}")
    
    def _extrair_importancia_features(self):
        """
        Extrai e armazena a importância de cada feature para o modelo.
        """
        regressor = self.pipeline.named_steps['regressor']
        
        # Para modelos lineares, extrai coeficientes
        if hasattr(regressor, 'coef_'):
            coefs = regressor.coef_
            for i, feature in enumerate(FEATURE_NAMES):
                if i < len(coefs):
                    self.estatisticas['coeficientes'][feature] = float(coefs[i])
            
            # Adiciona o intercepto
            if hasattr(regressor, 'intercept_'):
                self.estatisticas['coeficientes']['intercepto'] = float(regressor.intercept_)
            
            logger.info(f"Coeficientes extraídos: {self.estatisticas['coeficientes']}")
        
        # Para modelos baseados em árvores, extrai importância
        if hasattr(regressor, 'feature_importances_'):
            importances = regressor.feature_importances_
            for i, feature in enumerate(FEATURE_NAMES):
                if i < len(importances):
                    self.estatisticas['importancia_features'][feature] = float(importances[i])
            
            logger.info(f"Importância de features extraída: {self.estatisticas['importancia_features']}")
    
    def prever(self, X: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Realiza previsões de preços com intervalo de confiança.
        
        Args:
            X: Matriz de features para previsão
            
        Returns:
            Tuple contendo previsões e informações adicionais
        """
        # Verifica se o modelo foi treinado
        if not self.esta_treinado():
            raise ValueError("O modelo ainda não foi treinado")
        
        # Realiza previsão
        previsoes = self.pipeline.predict(X)
        
        # Informações adicionais
        info_previsao = {
            'confianca': []  # Inicializa lista de intervalos de confiança
        }
        
        # Para cada previsão, calcula um intervalo de confiança simples (±10%)
        for pred in previsoes:
            info_previsao['confianca'].append((float(pred * 0.9), float(pred * 1.1)))
        
        return previsoes, info_previsao
    
    def esta_treinado(self) -> bool:
        """
        Verifica se o modelo foi treinado.
        
        Returns:
            bool: True se o modelo foi treinado
        """
        if self.pipeline is None:
            return False
            
        regressor = self.pipeline.named_steps['regressor']
        
        # Verifica atributos que indicam treinamento
        if hasattr(regressor, 'coef_'):
            return True
        if hasattr(regressor, 'feature_importances_'):
            return True
            
        return False
    
    def _salvar_modelo(self):
        """
        Salva o modelo treinado em disco.
        """
        try:
            joblib.dump(self.pipeline, self.caminho_modelo)
            logger.info(f"Modelo salvo em {self.caminho_modelo}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {e}")
            return False
    
    def obter_informacoes(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo.
        
        Returns:
            Dict com informações do modelo
        """
        return {
            'tipo': self.tipo_modelo,
            'treinado': self.esta_treinado(),
            'estatisticas': self.estatisticas,
            'features_suportadas': FEATURE_NAMES
        } 