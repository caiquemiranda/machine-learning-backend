#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

app = Flask(__name__)

# Diretório para salvar o modelo
MODEL_DIR = 'modelos'
MODEL_PATH = os.path.join(MODEL_DIR, 'modelo_regressao.pkl')

# Criar diretório se não existir
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Função para carregar o modelo, se existir
def carregar_modelo():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
    return LinearRegression()

# Inicializa o modelo
modelo = carregar_modelo()

# Dados de exemplo para treinamento (área da casa x preço)
X_treino = np.array([[50], [75], [100], [125], [150], [175], [200]]).reshape(-1, 1)
y_treino = np.array([500000, 700000, 900000, 1100000, 1300000, 1500000, 1700000])

# Rota principal
@app.route('/')
def index():
    return "API de Previsão de Preços de Imóveis com Persistência"

# Rota para treinar o modelo
@app.route('/treinar', methods=['GET'])
def treinar():
    # Treina o modelo com os dados de exemplo
    modelo.fit(X_treino, y_treino)
    
    # Salva o modelo treinado
    joblib.dump(modelo, MODEL_PATH)
    
    return jsonify({
        "mensagem": "Modelo treinado e salvo com sucesso", 
        "caminho_modelo": MODEL_PATH,
        "coeficiente": float(modelo.coef_[0]),
        "intercepto": float(modelo.intercept_)
    })

# Rota para fazer previsões
@app.route('/prever', methods=['POST'])
def prever():
    try:
        # Obtém os dados do request
        dados = request.get_json()
        area = dados.get('area', 0)
        
        # Verifica se o modelo foi treinado
        if not hasattr(modelo, 'coef_'):
            return jsonify({"erro": "O modelo ainda não foi treinado"}), 400
        
        # Faz a previsão
        area_array = np.array([area]).reshape(-1, 1)
        preco_previsto = modelo.predict(area_array)[0]
        
        return jsonify({
            "area": area,
            "preco_previsto": float(preco_previsto)
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

# Rota para verificar status do modelo
@app.route('/status', methods=['GET'])
def status():
    modelo_existe = os.path.exists(MODEL_PATH)
    modelo_treinado = hasattr(modelo, 'coef_')
    
    return jsonify({
        "modelo_salvo": modelo_existe,
        "modelo_carregado": modelo_treinado,
        "coeficiente": float(modelo.coef_[0]) if modelo_treinado else None,
        "intercepto": float(modelo.intercept_) if modelo_treinado else None
    })

if __name__ == '__main__':
    app.run(debug=True) 