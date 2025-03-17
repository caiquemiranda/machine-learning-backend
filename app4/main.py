#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, root_validator
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
import joblib
import os
import uvicorn
from typing import Dict, Optional, List, Union, Any, Tuple

# Diretório para salvar o modelo e os pré-processadores
MODEL_DIR = 'modelos'
MODEL_PATH = os.path.join(MODEL_DIR, 'modelo_pipeline.pkl')

# Criar diretório se não existir
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Modelos de dados para a API com validação avançada
class PrevisaoInput(BaseModel):
    area: float = Field(..., description="Área do imóvel em metros quadrados", gt=0)
    quartos: Optional[int] = Field(None, description="Número de quartos", ge=0)
    banheiros: Optional[int] = Field(None, description="Número de banheiros", ge=0)
    idade_imovel: Optional[int] = Field(None, description="Idade do imóvel em anos", ge=0)
    
    @validator('area')
    def area_deve_ser_razoavel(cls, v):
        if v > 10000:
            raise ValueError("Área muito grande, por favor verifique a unidade de medida (metros quadrados)")
        return v
    
    @validator('quartos', 'banheiros')
    def valores_devem_ser_razoaveis(cls, v):
        if v is not None and v > 20:
            raise ValueError("Valor parece muito alto, por favor verifique")
        return v
    
    @root_validator
    def verificar_valores(cls, values):
        # Lógica mais complexa de validação
        area = values.get('area')
        quartos = values.get('quartos')
        
        if quartos is not None and area is not None:
            if quartos > 0 and area / quartos < 8:
                raise ValueError("A proporção de área por quarto parece muito pequena")
        
        return values

class PrevisaoOutput(BaseModel):
    area: float
    quartos: Optional[int] = None
    banheiros: Optional[int] = None
    idade_imovel: Optional[int] = None
    preco_previsto: float
    faixa_confianca: Tuple[float, float]

class TreinamentoInput(BaseModel):
    features: List[Dict[str, Any]] = Field(..., description="Lista de características dos imóveis")
    precos: List[float] = Field(..., description="Lista de preços correspondentes aos imóveis")
    
    @validator('features')
    def validar_features(cls, v):
        if not v:
            raise ValueError("A lista de features não pode estar vazia")
        
        # Verifica as chaves nas features
        required_keys = {'area'}
        optional_keys = {'quartos', 'banheiros', 'idade_imovel'}
        
        for i, item in enumerate(v):
            # Verifica chaves obrigatórias
            if not required_keys.issubset(item.keys()):
                raise ValueError(f"Item {i}: faltando chaves obrigatórias. Obrigatórias: {required_keys}")
            
            # Verifica se todas as chaves são conhecidas
            unknown_keys = set(item.keys()) - required_keys - optional_keys
            if unknown_keys:
                raise ValueError(f"Item {i}: chaves desconhecidas detectadas: {unknown_keys}")
        
        return v
    
    @validator('precos')
    def validar_precos(cls, v, values):
        if 'features' in values and len(values['features']) != len(v):
            raise ValueError("O número de features e preços deve ser igual")
        
        if any(preco <= 0 for preco in v):
            raise ValueError("Todos os preços devem ser positivos")
            
        return v

class StatusOutput(BaseModel):
    modelo_salvo: bool
    modelo_carregado: bool
    features_suportadas: List[str]
    numero_amostras_treinamento: Optional[int] = None

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API de Previsão de Preços de Imóveis",
    description="Uma API RESTful com pré-processamento e validação de dados",
    version="4.0.0"
)

# Função para criar o pipeline de pré-processamento
def criar_pipeline():
    # Processamento numérico
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Processamento para cada tipo de coluna
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, ['area', 'quartos', 'banheiros', 'idade_imovel'])
        ]
    )
    
    # Pipeline completo
    return Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

# Função para carregar o modelo
def carregar_modelo():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH), True
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
    
    # Retorna um novo pipeline se não conseguir carregar
    pipeline = criar_pipeline()
    return pipeline, False

# Inicializa o modelo
modelo, modelo_carregado = carregar_modelo()
numero_amostras_treino = 0

# Rota principal
@app.get("/")
def index():
    return {"mensagem": "API de Previsão de Preços de Imóveis v4.0 com Pré-processamento"}

# Dependência para preparar dados de entrada para previsão
def preparar_dados_previsao(dados: PrevisaoInput):
    # Converte o input para um formato adequado para o modelo
    feature_dict = dados.dict()
    X = np.array([[
        feature_dict['area'],
        feature_dict.get('quartos', np.nan),
        feature_dict.get('banheiros', np.nan),
        feature_dict.get('idade_imovel', np.nan)
    ]])
    
    feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
    
    return X, feature_names, feature_dict

# Rota para treinar o modelo com dados personalizados
@app.post("/treinar", response_model=Dict[str, Union[str, int, float]])
def treinar(dados: TreinamentoInput):
    global numero_amostras_treino
    
    try:
        # Extrai features dos dados de treinamento
        feature_list = []
        for item in dados.features:
            feature_list.append([
                item['area'],
                item.get('quartos', np.nan),
                item.get('banheiros', np.nan),
                item.get('idade_imovel', np.nan)
            ])
        
        # Prepara os dados de treinamento
        X = np.array(feature_list)
        y = np.array(dados.precos)
        
        # Prepara feature names para o pipeline
        feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
        modelo.steps[0][1].transformers[0][2] = feature_names
        
        # Treina o modelo
        modelo.fit(X, y)
        
        # Atualiza contador de amostras
        numero_amostras_treino = len(X)
        
        # Salva o modelo treinado
        joblib.dump(modelo, MODEL_PATH)
        
        # Calcula R² para informar qualidade do modelo
        r2 = modelo.score(X, y)
        
        return {
            "mensagem": "Modelo treinado e salvo com sucesso", 
            "num_amostras": len(X),
            "r2_score": float(r2),
            "features_utilizadas": feature_names
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Rota para fazer previsões
@app.post("/prever", response_model=PrevisaoOutput)
def prever(X_dados: Tuple[np.ndarray, List[str], Dict] = Depends(preparar_dados_previsao)):
    try:
        X, feature_names, feature_dict = X_dados
        
        # Verifica se o modelo foi treinado
        if not hasattr(modelo.steps[-1][1], 'coef_'):
            raise HTTPException(
                status_code=400, 
                detail="O modelo ainda não foi treinado"
            )
        
        # Faz a previsão
        preco_previsto = modelo.predict(X)[0]
        
        # Calculando uma faixa de confiança simples (±10%)
        faixa_inferior = preco_previsto * 0.9
        faixa_superior = preco_previsto * 1.1
        
        return PrevisaoOutput(
            area=feature_dict['area'],
            quartos=feature_dict.get('quartos'),
            banheiros=feature_dict.get('banheiros'),
            idade_imovel=feature_dict.get('idade_imovel'),
            preco_previsto=float(preco_previsto),
            faixa_confianca=(float(faixa_inferior), float(faixa_superior))
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rota para obter o status do modelo
@app.get("/status", response_model=StatusOutput)
def status():
    modelo_existe = os.path.exists(MODEL_PATH)
    modelo_treinado = hasattr(modelo.steps[-1][1], 'coef_')
    
    return StatusOutput(
        modelo_salvo=modelo_existe,
        modelo_carregado=modelo_treinado,
        features_suportadas=['area', 'quartos', 'banheiros', 'idade_imovel'],
        numero_amostras_treinamento=numero_amostras_treino if modelo_treinado else None
    )

# Executar a aplicação diretamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 