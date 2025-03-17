#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError

from .config import Config
from .database.database import init_db
from .ml.models import ModeloPrecoImovel
from .api.endpoints import router as api_router
from .api.middleware import setup_middlewares
from .utils.logger import get_logger

# Configuração do logger
logger = get_logger(nome_app="main")

def custom_openapi():
    """
    Personaliza a documentação OpenAPI da aplicação.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=Config.API_TITLE,
        version=Config.API_VERSION,
        description=Config.API_DESCRIPTION,
        routes=app.routes,
    )
    
    # Adicionar informações extras
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Adicionar tags
    openapi_schema["tags"] = [
        {
            "name": "Previsão",
            "description": "Endpoints para previsão de preços de imóveis"
        },
        {
            "name": "Treinamento",
            "description": "Endpoints para treinamento de modelos"
        },
        {
            "name": "Tarefas",
            "description": "Endpoints para gerenciamento de tarefas assíncronas"
        },
        {
            "name": "Status",
            "description": "Endpoints para verificação de status da API e serviços"
        }
    ]
    
    # Adicionar descrição de recursos
    openapi_schema["info"]["description"] = """
    # API de Previsão de Preços de Imóveis v9.0
    
    Esta API permite prever preços de imóveis com base em suas características.
    
    ## Recursos
    
    * **Processamento Assíncrono**: Tarefas demoradas são executadas em background
    * **Celery + Redis**: Sistema de filas para processamento distribuído
    * **Múltiplos Algoritmos**: Suporte para diferentes algoritmos de ML
    * **Monitoramento**: Acompanhamento de tarefas e status do sistema
    
    ## Autenticação
    
    A API utiliza autenticação via API Key quando habilitada.
    Adicione o header `X-API-Key` com a chave configurada.
    """
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def create_app():
    """
    Cria e configura a aplicação FastAPI.
    """
    # Criar aplicação
    app = FastAPI(
        title=Config.API_TITLE,
        description=Config.API_DESCRIPTION,
        version=Config.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Configurar documentação OpenAPI personalizada
    app.openapi = custom_openapi
    
    # Configurar middlewares
    setup_middlewares(app)
    
    # Configurar tratamento de exceções
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Tratamento personalizado para erros de validação.
        """
        logger.warning(f"Erro de validação: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Erro de validação dos dados",
                "errors": exc.errors(),
                "body": exc.body
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Tratamento personalizado para exceções HTTP.
        """
        logger.warning(f"Exceção HTTP: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail
            }
        )
    
    # Incluir rotas da API
    app.include_router(api_router, prefix="")
    
    return app

# Criar aplicação
app = create_app()

# Inicializar serviço de ML
ml_service = ModeloPrecoImovel()
try:
    ml_service.carregar_modelo()
    logger.info("Modelo de ML carregado com sucesso")
except Exception as e:
    logger.warning(f"Não foi possível carregar o modelo de ML: {str(e)}")

# Verificar e criar tabelas do banco de dados
@app.on_event("startup")
async def startup_db_client():
    """
    Inicializa o banco de dados na inicialização da aplicação.
    """
    try:
        if init_db():
            logger.info("Banco de dados inicializado com sucesso")
        else:
            logger.error("Falha ao inicializar o banco de dados")
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")

if __name__ == "__main__":
    # Executar aplicação com uvicorn
    uvicorn.run(
        "app9.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    ) 