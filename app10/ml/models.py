#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns

from ..config import Config
from ..utils.logger import app_logger
from ..utils.metrics import MODEL_LOADED, measure_time, TRAINING_DURATION, PREDICTION_DURATION


class ModeloPrecoImovel:
    """
    Classe responsável pelo treinamento e predição de preços de imóveis.
    """
    
    def __init__(self):
        """
        Inicializa o modelo de previsão de preços de imóveis.
        """
        # Criação do diretório de modelos se não existir
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
        
        # Caminho para o modelo
        self.model_path = os.path.join(Config.MODELS_DIR, Config.MODEL_FILE)
        
        # Atributos do modelo
        self.modelo = None
        self.algoritmo = Config.DEFAULT_ALGORITHM
        self.scaler = StandardScaler()
        self.metricas = {}
        self.ultima_atualizacao = None
        
        # Mapeamento de algoritmos
        self.algoritmos = {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(random_state=42),
            "decision_tree": DecisionTreeRegressor(random_state=42),
            "gradient_boosting": GradientBoostingRegressor(random_state=42),
            "svr": SVR(),
            "elastic_net": ElasticNet(random_state=42)
        }
        
        # Colunas de features
        self.feature_columns = ['area', 'quartos', 'banheiros', 'garagem', 'idade']
        
        # Atualizar métrica de modelo carregado
        MODEL_LOADED.labels(model_type=self.algoritmo).set(0)
    
    @measure_time(TRAINING_DURATION, labels={"model_type": "default"})
    def treinar(self, dados: List[Dict[str, Any]], algoritmo: str = None) -> Dict[str, float]:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            dados: Lista de dicionários com os dados de treinamento
            algoritmo: Nome do algoritmo a ser utilizado. Se None, usa o padrão.
        
        Returns:
            Dict[str, float]: Métricas do modelo treinado
        """
        inicio = time.time()
        app_logger.info(f"Iniciando treinamento com algoritmo: {algoritmo or self.algoritmo}")
        
        try:
            # Preparar os dados
            df = pd.DataFrame(dados)
            
            # Verificar colunas necessárias
            for col in self.feature_columns + ['preco']:
                if col not in df.columns:
                    raise ValueError(f"Coluna {col} não encontrada nos dados de treinamento")
            
            # Separar features e target
            X = df[self.feature_columns]
            y = df['preco']
            
            # Dividir em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Selecionar algoritmo
            if algoritmo and algoritmo in self.algoritmos:
                self.algoritmo = algoritmo
            
            # Criar pipeline com scaler e modelo
            self.modelo = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', self.algoritmos[self.algoritmo])
            ])
            
            # Treinar o modelo
            self.modelo.fit(X_train, y_train)
            
            # Avaliar o modelo
            y_pred = self.modelo.predict(X_test)
            
            # Calcular métricas
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Armazenar métricas
            self.metricas = {
                'mae': mae,
                'mse': mse,
                'rmse': np.sqrt(mse),
                'r2': r2
            }
            
            # Salvar o modelo
            self.salvar_modelo()
            
            # Atualizar timestamp
            self.ultima_atualizacao = time.time()
            
            # Atualizar métrica de modelo carregado
            MODEL_LOADED.labels(model_type=self.algoritmo).set(1)
            
            # Calcular tempo de treinamento
            tempo_treinamento = time.time() - inicio
            
            app_logger.info(f"Treinamento concluído em {tempo_treinamento:.2f}s. Métricas: {self.metricas}")
            
            # Adicionar tempo de treinamento às métricas
            self.metricas['tempo_treinamento'] = tempo_treinamento
            
            return self.metricas
        
        except Exception as e:
            app_logger.error(f"Erro durante o treinamento: {str(e)}", exc_info=True)
            raise
    
    @measure_time(PREDICTION_DURATION, labels={"model_type": "default"})
    def prever(self, dados: Dict[str, Any]) -> Tuple[float, Optional[float]]:
        """
        Realiza uma previsão de preço com base nos dados fornecidos.
        
        Args:
            dados: Dicionário com os dados para previsão
        
        Returns:
            Tuple[float, Optional[float]]: Preço previsto e nível de confiança (se disponível)
        """
        inicio = time.time()
        app_logger.info(f"Iniciando previsão para dados: {dados}")
        
        try:
            # Verificar se o modelo está carregado
            if self.modelo is None:
                self.carregar_modelo()
            
            # Preparar os dados para predição
            df = pd.DataFrame([dados])
            
            # Verificar colunas necessárias
            for col in self.feature_columns:
                if col not in df.columns:
                    raise ValueError(f"Coluna {col} não encontrada nos dados de previsão")
            
            # Selecionar apenas as features relevantes na ordem correta
            X = df[self.feature_columns]
            
            # Fazer a predição
            preco_previsto = float(self.modelo.predict(X)[0])
            
            # Calcular nível de confiança (simplificado)
            confianca = None
            if hasattr(self.modelo, 'predict_proba'):
                try:
                    probs = self.modelo.predict_proba(X)
                    confianca = float(np.max(probs, axis=1)[0])
                except:
                    pass
            
            # Registrar tempo de previsão
            tempo_previsao = time.time() - inicio
            app_logger.info(f"Previsão concluída em {tempo_previsao:.4f}s. Resultado: {preco_previsto}")
            
            return preco_previsto, confianca
        
        except Exception as e:
            app_logger.error(f"Erro durante a previsão: {str(e)}", exc_info=True)
            raise
    
    def salvar_modelo(self):
        """
        Salva o modelo treinado no disco.
        """
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Salvar modelo, scaler, métricas e metadata
            joblib.dump({
                'modelo': self.modelo,
                'algoritmo': self.algoritmo,
                'metricas': self.metricas,
                'feature_columns': self.feature_columns,
                'timestamp': time.time()
            }, self.model_path)
            
            app_logger.info(f"Modelo salvo com sucesso em: {self.model_path}")
            return True
        except Exception as e:
            app_logger.error(f"Erro ao salvar modelo: {str(e)}", exc_info=True)
            return False
    
    def carregar_modelo(self):
        """
        Carrega o modelo do disco.
        
        Returns:
            bool: True se o modelo foi carregado com sucesso, False caso contrário
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(self.model_path):
                app_logger.warning(f"Arquivo de modelo não encontrado: {self.model_path}")
                return False
            
            # Carregar modelo
            data = joblib.load(self.model_path)
            
            # Extrair componentes
            self.modelo = data['modelo']
            self.algoritmo = data['algoritmo']
            self.metricas = data['metricas']
            self.feature_columns = data['feature_columns']
            self.ultima_atualizacao = data['timestamp']
            
            # Atualizar métrica de modelo carregado
            MODEL_LOADED.labels(model_type=self.algoritmo).set(1)
            
            app_logger.info(f"Modelo carregado com sucesso: {self.algoritmo}")
            return True
        
        except Exception as e:
            app_logger.error(f"Erro ao carregar modelo: {str(e)}", exc_info=True)
            return False
    
    def get_status(self):
        """
        Retorna o status atual do modelo.
        
        Returns:
            Dict: Status do modelo
        """
        return {
            'modelo_carregado': self.modelo is not None,
            'algoritmo': self.algoritmo,
            'metricas': self.metricas,
            'ultima_atualizacao': self.ultima_atualizacao
        }
    
    def gerar_visualizacoes(self, dados: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Gera visualizações para os dados de treinamento.
        
        Args:
            dados: Lista de dicionários com os dados de treinamento
        
        Returns:
            Dict[str, str]: Caminhos para as visualizações geradas
        """
        try:
            # Criar diretório para visualizações
            visualizacoes_dir = os.path.join(Config.MODELS_DIR, 'visualizacoes')
            os.makedirs(visualizacoes_dir, exist_ok=True)
            
            # Converter para DataFrame
            df = pd.DataFrame(dados)
            
            # Gerar visualizações
            visualizacoes = {}
            
            # 1. Histograma de preços
            plt.figure(figsize=(10, 6))
            sns.histplot(df['preco'], kde=True)
            plt.title('Distribuição dos Preços')
            plt.xlabel('Preço')
            plt.ylabel('Frequência')
            hist_path = os.path.join(visualizacoes_dir, 'histograma_precos.png')
            plt.savefig(hist_path)
            plt.close()
            visualizacoes['histograma_precos'] = hist_path
            
            # 2. Correlação entre variáveis
            plt.figure(figsize=(10, 8))
            corr = df.corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm')
            plt.title('Matriz de Correlação')
            corr_path = os.path.join(visualizacoes_dir, 'correlacao.png')
            plt.savefig(corr_path)
            plt.close()
            visualizacoes['correlacao'] = corr_path
            
            # 3. Preço vs. Área
            plt.figure(figsize=(10, 6))
            sns.scatterplot(x='area', y='preco', data=df)
            plt.title('Preço vs. Área')
            plt.xlabel('Área (m²)')
            plt.ylabel('Preço')
            area_path = os.path.join(visualizacoes_dir, 'preco_vs_area.png')
            plt.savefig(area_path)
            plt.close()
            visualizacoes['preco_vs_area'] = area_path
            
            app_logger.info(f"Visualizações geradas com sucesso: {list(visualizacoes.keys())}")
            return visualizacoes
        
        except Exception as e:
            app_logger.error(f"Erro ao gerar visualizações: {str(e)}", exc_info=True)
            return {} 