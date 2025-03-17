#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os
import uvicorn
from typing import Dict, Optional, List, Union

# Diretório para salvar o modelo
MODEL_DIR = 'modelos'
MODEL_PATH = os.path.join(MODEL_DIR, 'modelo_regressao.pkl')

# Criar diretório se não existir
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Modelos de dados para a API
class PrevisaoInput(BaseModel):
    area: float = Field(..., description="Área do imóvel em metros quadrados", gt=0)

class PrevisaoOutput(BaseModel):
    area: float
    preco_previsto: float

class TreinamentoInput(BaseModel):
    X: List[List[float]] = Field(..., description="Lista de características (apenas área neste exemplo)")
    y: List[float] = Field(..., description="Lista de preços correspondentes às áreas")

class StatusOutput(BaseModel):
    modelo_salvo: bool
    modelo_carregado: bool
    coeficiente: Optional[float] = None
    intercepto: Optional[float] = None

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API de Previsão de Preços de Imóveis",
    description="Uma API RESTful para treinar e realizar previsões com um modelo de regressão linear",
    version="3.0.0"
)

# Função para carregar o modelo
def carregar_modelo():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
    return LinearRegression()

# Inicializa o modelo
modelo = carregar_modelo()

# Dados de exemplo para treinamento
X_treino_exemplo = [[50], [75], [100], [125], [150], [175], [200]]
y_treino_exemplo = [500000, 700000, 900000, 1100000, 1300000, 1500000, 1700000]

# Rota principal
@app.get("/")
def index():
    return {"mensagem": "API de Previsão de Preços de Imóveis v3.0"}

# Rota para treinar o modelo com dados padrão
@app.post("/treinar/padrao", response_model=Dict[str, Union[str, float]])
def treinar_padrao():
    # Treina o modelo com os dados de exemplo
    X = np.array(X_treino_exemplo).reshape(-1, 1)
    y = np.array(y_treino_exemplo)
    
    modelo.fit(X, y)
    
    # Salva o modelo treinado
    joblib.dump(modelo, MODEL_PATH)
    
    return {
        "mensagem": "Modelo treinado e salvo com sucesso", 
        "caminho_modelo": MODEL_PATH,
        "coeficiente": float(modelo.coef_[0]),
        "intercepto": float(modelo.intercept_)
    }

# Rota para treinar o modelo com dados personalizados
@app.post("/treinar/personalizado", response_model=Dict[str, Union[str, float]])
def treinar_personalizado(dados: TreinamentoInput):
    try:
        # Prepara os dados de treinamento
        X = np.array(dados.X).reshape(-1, 1)
        y = np.array(dados.y)
        
        # Verifica se os tamanhos correspondem
        if len(X) != len(y):
            raise HTTPException(
                status_code=400, 
                detail="Os arrays X e y devem ter o mesmo tamanho"
            )
        
        # Treina o modelo
        modelo.fit(X, y)
        
        # Salva o modelo treinado
        joblib.dump(modelo, MODEL_PATH)
        
        return {
            "mensagem": "Modelo treinado e salvo com sucesso", 
            "num_amostras": len(X),
            "coeficiente": float(modelo.coef_[0]),
            "intercepto": float(modelo.intercept_)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Rota para fazer previsões
@app.post("/prever", response_model=PrevisaoOutput)
def prever(dados: PrevisaoInput):
    try:
        # Verifica se o modelo foi treinado
        if not hasattr(modelo, 'coef_'):
            raise HTTPException(
                status_code=400, 
                detail="O modelo ainda não foi treinado"
            )
        
        # Faz a previsão
        area_array = np.array([[dados.area]])
        preco_previsto = modelo.predict(area_array)[0]
        
        return PrevisaoOutput(
            area=dados.area,
            preco_previsto=float(preco_previsto)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rota para obter o status do modelo
@app.get("/status", response_model=StatusOutput)
def status():
    modelo_existe = os.path.exists(MODEL_PATH)
    modelo_treinado = hasattr(modelo, 'coef_')
    
    return StatusOutput(
        modelo_salvo=modelo_existe,
        modelo_carregado=modelo_treinado,
        coeficiente=float(modelo.coef_[0]) if modelo_treinado else None,
        intercepto=float(modelo.intercept_) if modelo_treinado else None
    )

# Executar a aplicação diretamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 