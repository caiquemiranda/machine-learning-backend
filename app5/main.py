#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, Body, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
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
import logging
import time
import traceback
import json
from datetime import datetime
from typing import Dict, Optional, List, Union, Any, Tuple
import uuid

# Configuração de logging
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'api.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('imoveis-api')

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
    request_id: str
    timestamp: str
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
    estatisticas_api: Dict[str, Any]

class ErrorResponse(BaseModel):
    request_id: str
    timestamp: str
    error: str
    detail: str
    path: str
    http_status: int

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API de Previsão de Preços de Imóveis",
    description="Uma API RESTful com logging e tratamento de erros avançado",
    version="5.0.0"
)

# Adiciona middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estatísticas da API
api_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "previsoes_realizadas": 0,
    "treinamentos_realizados": 0,
    "ultimo_erro": None,
    "uptime_start": datetime.now().isoformat()
}

# Middleware para logging e estatísticas
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Gera um ID de requisição único
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Registra início da requisição
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    logger.info(f"Request {request_id} started: {method} {path}")
    api_stats["total_requests"] += 1
    
    try:
        # Processa a requisição
        response = await call_next(request)
        
        # Registra conclusão com sucesso
        process_time = time.time() - start_time
        logger.info(f"Request {request_id} completed: {method} {path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        
        if response.status_code < 400:
            api_stats["successful_requests"] += 1
        else:
            api_stats["failed_requests"] += 1
            
        return response
    except Exception as e:
        # Registra erro
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed: {method} {path} - Error: {str(e)} - Time: {process_time:.4f}s")
        logger.error(traceback.format_exc())
        
        api_stats["failed_requests"] += 1
        api_stats["ultimo_erro"] = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "path": path,
            "error": str(e)
        }
        
        # Retorna erro 500 para exceções não tratadas
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                request_id=request_id,
                timestamp=datetime.now().isoformat(),
                error="Internal Server Error",
                detail=str(e),
                path=path,
                http_status=500
            ).dict()
        )

# Manipulador de erros de validação
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Formata os erros de validação
    errors = []
    for error in exc.errors():
        error_msg = f"Campo '{'.'.join(error['loc'][1:])}': {error['msg']}"
        errors.append(error_msg)
    
    # Registra erro de validação
    error_detail = "; ".join(errors)
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"Request {request_id} validation error: {error_detail}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            error="Validation Error",
            detail=error_detail,
            path=request.url.path,
            http_status=422
        ).dict()
    )

# Manipulador para erros HTTP
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"Request {request_id} HTTP error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            error=f"HTTP Error {exc.status_code}",
            detail=exc.detail,
            path=request.url.path,
            http_status=exc.status_code
        ).dict()
    )

# Função para criar o pipeline de pré-processamento
def criar_pipeline():
    logger.info("Criando novo pipeline de ML")
    
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
            logger.info(f"Tentando carregar modelo de {MODEL_PATH}")
            pipeline = joblib.load(MODEL_PATH)
            logger.info("Modelo carregado com sucesso")
            return pipeline, True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            logger.error(traceback.format_exc())
    else:
        logger.info(f"Arquivo de modelo não encontrado em {MODEL_PATH}")
    
    # Retorna um novo pipeline se não conseguir carregar
    return criar_pipeline(), False

# Inicializa o modelo
modelo, modelo_carregado = carregar_modelo()
numero_amostras_treino = 0

# Rota principal
@app.get("/")
def index():
    logger.info("Endpoint raiz acessado")
    return {"mensagem": "API de Previsão de Preços de Imóveis v5.0 com Logging e Tratamento de Erros"}

# Dependência para preparar dados de entrada para previsão
def preparar_dados_previsao(dados: PrevisaoInput, request: Request):
    logger.debug(f"Preparando dados para previsão: {dados.dict()}")
    
    # Converte o input para um formato adequado para o modelo
    feature_dict = dados.dict()
    X = np.array([[
        feature_dict['area'],
        feature_dict.get('quartos', np.nan),
        feature_dict.get('banheiros', np.nan),
        feature_dict.get('idade_imovel', np.nan)
    ]])
    
    feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
    
    return X, feature_names, feature_dict, request.state.request_id

# Rota para treinar o modelo com dados personalizados
@app.post("/treinar", response_model=Dict[str, Union[str, int, float]])
def treinar(dados: TreinamentoInput, request: Request):
    global numero_amostras_treino
    request_id = request.state.request_id
    
    logger.info(f"Request {request_id}: Iniciando treinamento com {len(dados.features)} amostras")
    
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
        
        logger.debug(f"Request {request_id}: Dados de treinamento preparados: X shape {X.shape}, y shape {y.shape}")
        
        # Prepara feature names para o pipeline
        feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
        modelo.steps[0][1].transformers[0][2] = feature_names
        
        # Treina o modelo
        logger.info(f"Request {request_id}: Iniciando fit do modelo")
        start_time = time.time()
        modelo.fit(X, y)
        training_time = time.time() - start_time
        logger.info(f"Request {request_id}: Modelo treinado em {training_time:.4f}s")
        
        # Atualiza contador de amostras
        numero_amostras_treino = len(X)
        
        # Salva o modelo treinado
        logger.info(f"Request {request_id}: Salvando modelo em {MODEL_PATH}")
        joblib.dump(modelo, MODEL_PATH)
        
        # Calcula R² para informar qualidade do modelo
        r2 = modelo.score(X, y)
        logger.info(f"Request {request_id}: Modelo treinado com R² de {r2:.4f}")
        
        # Atualiza estatísticas
        api_stats["treinamentos_realizados"] += 1
        
        return {
            "request_id": request_id,
            "mensagem": "Modelo treinado e salvo com sucesso", 
            "num_amostras": len(X),
            "r2_score": float(r2),
            "training_time_seconds": training_time,
            "features_utilizadas": feature_names
        }
    
    except Exception as e:
        logger.error(f"Request {request_id}: Erro durante treinamento - {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

# Rota para fazer previsões
@app.post("/prever", response_model=PrevisaoOutput)
def prever(dados_processados: Tuple[np.ndarray, List[str], Dict, str] = Depends(preparar_dados_previsao)):
    X, feature_names, feature_dict, request_id = dados_processados
    
    logger.info(f"Request {request_id}: Realizando previsão para imóvel de {feature_dict['area']}m²")
    
    try:
        # Verifica se o modelo foi treinado
        if not hasattr(modelo.steps[-1][1], 'coef_'):
            logger.error(f"Request {request_id}: Tentativa de previsão com modelo não treinado")
            raise HTTPException(
                status_code=400, 
                detail="O modelo ainda não foi treinado"
            )
        
        # Faz a previsão
        start_time = time.time()
        preco_previsto = modelo.predict(X)[0]
        predict_time = time.time() - start_time
        
        logger.info(f"Request {request_id}: Previsão realizada em {predict_time:.4f}s: R$ {preco_previsto:.2f}")
        
        # Calculando uma faixa de confiança simples (±10%)
        faixa_inferior = preco_previsto * 0.9
        faixa_superior = preco_previsto * 1.1
        
        # Atualiza estatísticas
        api_stats["previsoes_realizadas"] += 1
        
        return PrevisaoOutput(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
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
        logger.error(f"Request {request_id}: Erro durante previsão - {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Rota para obter o status do modelo
@app.get("/status", response_model=StatusOutput)
def status(request: Request):
    request_id = request.state.request_id
    logger.info(f"Request {request_id}: Verificando status do modelo")
    
    modelo_existe = os.path.exists(MODEL_PATH)
    modelo_treinado = hasattr(modelo.steps[-1][1], 'coef_')
    
    # Calcula uptime
    uptime_seconds = (datetime.now() - datetime.fromisoformat(api_stats["uptime_start"])).total_seconds()
    
    # Adiciona estatísticas atualizadas
    estatisticas_atualizadas = {
        **api_stats,
        "uptime_seconds": uptime_seconds
    }
    
    return StatusOutput(
        modelo_salvo=modelo_existe,
        modelo_carregado=modelo_treinado,
        features_suportadas=['area', 'quartos', 'banheiros', 'idade_imovel'],
        numero_amostras_treinamento=numero_amostras_treino if modelo_treinado else None,
        estatisticas_api=estatisticas_atualizadas
    )

# Rota para limpar logs (apenas para testes/desenvolvimento)
@app.post("/admin/limpar-logs", status_code=204)
def limpar_logs(request: Request):
    request_id = request.state.request_id
    logger.warning(f"Request {request_id}: Limpando logs (solicitado por admin)")
    
    try:
        with open(os.path.join(LOG_DIR, 'api.log'), 'w') as f:
            f.write(f"Logs limpos em {datetime.now().isoformat()} - Request ID: {request_id}\n")
        return None
    except Exception as e:
        logger.error(f"Request {request_id}: Erro ao limpar logs - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao limpar logs: {str(e)}")

# Executar a aplicação diretamente
if __name__ == "__main__":
    logger.info("Iniciando aplicação")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 