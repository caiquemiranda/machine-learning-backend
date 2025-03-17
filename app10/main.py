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
from prometheus_client import make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app10.config import Config
from app10.database.database import init_db
from app10.ml.models import ModeloPrecoImovel
from app10.api.endpoints import router as api_router
from app10.api.middleware import setup_middlewares
from app10.utils.logger import app_logger
from app10.utils.metrics import HTTP_REQUEST_COUNTER, ERROR_COUNTER

# Configuração do Sentry se o DSN estiver disponível
if Config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        environment=Config.SENTRY_ENVIRONMENT,
        traces_sample_rate=0.1,
        enable_tracing=True,
    )


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
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI.
    
    Returns:
        FastAPI: Aplicação configurada
    """
    # Criar diretórios necessários
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    
    # Criar aplicação FastAPI
    app = FastAPI(
        title=Config.API_TITLE,
        description=Config.API_DESCRIPTION,
        version=Config.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Personalizar documentação OpenAPI
    app.openapi = custom_openapi
    
    # Configurar middlewares
    setup_middlewares(app)
    
    # Adicionar Sentry middleware
    if Config.SENTRY_DSN:
        app.add_middleware(SentryAsgiMiddleware)
    
    # Registrar rotas
    app.include_router(api_router)
    
    # Handler para erros de validação
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handler para erros de validação de requisição.
        """
        app_logger.warning(f"Erro de validação: {str(exc)}")
        ERROR_COUNTER.labels(type="validation", location="request").inc()
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body},
        )
    
    # Handler para exceções não tratadas
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handler para exceções não tratadas.
        """
        app_logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
        ERROR_COUNTER.labels(type="unhandled", location="request").inc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"},
        )
    
    return app


# Criar aplicação
app = create_app()

# Inicializar serviço de ML
ml_service = ModeloPrecoImovel()
try:
    ml_service.carregar_modelo()
    app_logger.info("Modelo de ML carregado com sucesso")
except Exception as e:
    app_logger.warning(f"Não foi possível carregar o modelo de ML: {str(e)}")

# Verificar e criar tabelas do banco de dados
@app.on_event("startup")
async def startup_db_client():
    """
    Inicializa o banco de dados na inicialização da aplicação.
    """
    try:
        if init_db():
            app_logger.info("Banco de dados inicializado com sucesso")
        else:
            app_logger.error("Falha ao inicializar o banco de dados")
    except Exception as e:
        app_logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")


if __name__ == "__main__":
    # Executar aplicação com uvicorn
    uvicorn.run(
        "app10.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    ) 