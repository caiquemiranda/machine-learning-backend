#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Importações dos módulos da aplicação
from database.database import criar_tabelas, get_db
from utils.logger import Logger
from ml.models import ModeloPrecoImovel
from api.middleware import LoggingMiddleware, SimpleAuthMiddleware
from api.endpoints import router, ml_service, logger

def custom_openapi():
    """Personaliza a documentação OpenAPI"""
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="API Previsão Preços Imóveis",
        version="8.0.0",
        description="API de machine learning para previsão de preços de imóveis",
        routes=app.routes
    )
    
    # Personalização adicional do esquema OpenAPI
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def create_app():
    """Cria e configura a aplicação FastAPI"""
    _app = FastAPI(
        title="API de Previsão de Preços de Imóveis",
        description="Uma API para prever preços de imóveis usando machine learning.",
        version="8.0.0"
    )
    
    # Configura CORS
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Inicializa o logger
    log_manager = Logger(nome_app="imoveis-api-v8")
    _logger = log_manager.get_logger()
    
    # Configura o middleware de logging
    _app.add_middleware(LoggingMiddleware, logger=_logger)
    
    # Configuração opcional de autenticação
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        _app.add_middleware(
            SimpleAuthMiddleware, 
            api_key=os.getenv("API_KEY", "chave_secreta")
        )
    
    @_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler para erros de validação"""
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error["loc"],
                "msg": error["msg"],
                "type": error["type"]
            })
            
        return JSONResponse(
            status_code=422,
            content={
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "timestamp": datetime.now().isoformat(),
                "error": "Validation Error",
                "detail": errors,
                "path": request.url.path,
                "http_status": 422
            }
        )
    
    @_app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handler para erros HTTP"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "timestamp": datetime.now().isoformat(),
                "error": exc.detail,
                "detail": str(exc.detail),
                "path": request.url.path,
                "http_status": exc.status_code
            }
        )
        
    # Inicializa o serviço de ML
    _ml_service = ModeloPrecoImovel(logger=_logger)
    
    # Carrega modelo existente se disponível
    try:
        if _ml_service.carregar_modelo():
            _logger.info("Modelo carregado com sucesso")
        else:
            _logger.warning("Nenhum modelo encontrado para carregar")
    except Exception as e:
        _logger.error(f"Erro ao carregar modelo: {str(e)}")
        
    # Injeção de dependências para os endpoints
    # Isso evita a importação circular completa
    global ml_service, logger
    ml_service = _ml_service
    logger = _logger
    
    # Inclui os endpoints
    _app.include_router(router)
    
    # Customiza OpenAPI
    _app.openapi = custom_openapi
    
    return _app

# Cria as tabelas do banco de dados
try:
    criar_tabelas()
    print("Tabelas do banco de dados criadas/verificadas com sucesso")
except Exception as e:
    print(f"Erro ao criar tabelas: {str(e)}")
    
# Inicializa a aplicação
app = create_app()

if __name__ == "__main__":
    # Executa o servidor
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 