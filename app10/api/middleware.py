#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from ..config import Config
from ..utils.logger import app_logger
from ..utils.metrics import track_requests

# Configuração para autenticação com API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Middleware para autenticação com API Key
async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Verifica se a API Key fornecida é válida.
    
    Args:
        api_key (str): API Key fornecida no header X-API-Key
    
    Raises:
        HTTPException: Se a API Key for inválida ou não fornecida
    """
    if not Config.API_KEY_ENABLED:
        return
    
    if api_key != Config.API_KEY:
        app_logger.warning(f"Tentativa de acesso com API Key inválida: {api_key}")
        raise HTTPException(
            status_code=403,
            detail="API Key inválida ou não fornecida"
        )

# Middleware para logging de requisições
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requisições HTTP.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log da requisição recebida
        app_logger.info(
            f"Requisição recebida: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calcular duração da requisição
            duration = time.time() - start_time
            
            # Log da resposta
            app_logger.info(
                f"Resposta enviada: {response.status_code} em {duration:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            # Registrar métricas
            track_requests(response, request, duration)
            
            return response
        except Exception as e:
            # Log de erro
            app_logger.error(
                f"Erro ao processar requisição: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

# Middleware para métricas Prometheus
metrics_app = make_asgi_app()

def setup_middlewares(app: FastAPI):
    """
    Configura os middlewares da aplicação.
    
    Args:
        app (FastAPI): Aplicação FastAPI
    """
    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware de logging
    app.add_middleware(LoggingMiddleware)
    
    # Middleware para métricas Prometheus
    if Config.PROMETHEUS_ENABLED:
        app.mount("/metrics", metrics_app) 