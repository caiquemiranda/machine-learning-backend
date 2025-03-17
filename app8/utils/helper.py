#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import io
from datetime import datetime
import base64
from typing import Dict, List, Any, Optional, Union

class NumpyEncoder(json.JSONEncoder):
    """
    Encoder JSON personalizado para lidar com tipos numpy
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)

def json_serialize(obj):
    """
    Serializa um objeto para JSON, tratando tipos especiais
    """
    return json.dumps(obj, cls=NumpyEncoder)

def create_feature_matrix(dados_dict: List[Dict]) -> np.ndarray:
    """
    Cria uma matriz de features a partir de um dicionário
    
    Args:
        dados_dict: Lista de dicionários com dados dos imóveis
        
    Returns:
        Matriz numpy com as features
    """
    features = []
    
    for imovel in dados_dict:
        feature = [
            imovel.get('area', 0),
            imovel.get('quartos', np.nan),
            imovel.get('banheiros', np.nan),
            imovel.get('idade_imovel', np.nan)
        ]
        features.append(feature)
    
    return np.array(features)

def gerar_grafico_correlacao(X, y, feature_names, preco_nome="preco"):
    """
    Gera uma matriz de correlação e retorna como imagem base64
    
    Args:
        X: Matriz de features
        y: Array de targets (preços)
        feature_names: Nomes das features
        preco_nome: Nome da coluna de preço
        
    Returns:
        String base64 da imagem do gráfico
    """
    # Cria DataFrame com features e preço
    df = pd.DataFrame(X, columns=feature_names)
    df[preco_nome] = y
    
    # Calcula a matriz de correlação
    corr = df.corr()
    
    # Configura o gráfico
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Matriz de Correlação')
    
    # Salva o gráfico em um buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    # Converte para base64
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"

def gerar_grafico_dispersao(X, y, feature_index, feature_name, preco_nome="preco"):
    """
    Gera um gráfico de dispersão de uma feature vs preço
    
    Args:
        X: Matriz de features
        y: Array de targets (preços)
        feature_index: Índice da feature a ser plotada
        feature_name: Nome da feature
        preco_nome: Nome da coluna de preço
        
    Returns:
        String base64 da imagem do gráfico
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(X[:, feature_index], y, alpha=0.6)
    
    # Adiciona linha de tendência
    z = np.polyfit(X[:, feature_index], y, 1)
    p = np.poly1d(z)
    plt.plot(X[:, feature_index], p(X[:, feature_index]), "r--")
    
    plt.xlabel(feature_name)
    plt.ylabel(preco_nome)
    plt.title(f'Relação entre {feature_name} e {preco_nome}')
    plt.grid(True, alpha=0.3)
    
    # Salva o gráfico em um buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    # Converte para base64
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_str}" 