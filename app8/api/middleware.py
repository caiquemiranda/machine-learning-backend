#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import json
from typing import Callable
from datetime import datetime

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requisições e respostas
    """
    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger
        
    async def dispatch(self, request: Request, call_next: Callable):
        # Gera um ID único para a requisição
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Registra o início da requisição
        start_time = time.time()
        self.logger.info(
            f"Requisição iniciada: {request_id} - {request.method} {request.url.path}"
        )
        
        # Tenta processar a requisição
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Adiciona headers com informações de timing
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # Registra o fim da requisição
            status_code = response.status_code
            self.logger.info(
                f"Requisição concluída: {request_id} - {request.method} {request.url.path} "
                f"- Status: {status_code} - Tempo: {process_time:.4f}s"
            )
            
            return response
        except Exception as e:
            # Se ocorrer uma exceção durante o processamento
            process_time = time.time() - start_time
            self.logger.error(
                f"Erro na requisição: {request_id} - {request.method} {request.url.path} "
                f"- Erro: {str(e)} - Tempo: {process_time:.4f}s"
            )
            
            # Retorna uma resposta de erro padronizada
            return JSONResponse(
                status_code=500,
                content={
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Internal Server Error",
                    "detail": str(e),
                    "path": request.url.path,
                    "http_status": 500
                }
            )

class SimpleAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware simples para autenticação baseada em API key
    Usado apenas para demonstração - não adequado para produção
    """
    def __init__(self, app, api_key="chave_secreta", exclude_paths=None):
        super().__init__(app)
        self.api_key = api_key
        self.exclude_paths = exclude_paths or ["/", "/docs", "/redoc", "/openapi.json"]
        
    async def dispatch(self, request: Request, call_next: Callable):
        # Verifica se o caminho está excluído da autenticação
        path = request.url.path
        if any(path.startswith(excl) for excl in self.exclude_paths):
            return await call_next(request)
            
        # Verifica a API key no header ou query parameter
        api_key_header = request.headers.get("X-API-Key")
        api_key_query = request.query_params.get("api_key")
        
        if api_key_header == self.api_key or api_key_query == self.api_key:
            return await call_next(request)
        
        # Retorna erro se a autenticação falhar
        return JSONResponse(
            status_code=401,
            content={
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "error": "Unauthorized",
                "detail": "API key inválida ou não fornecida",
                "path": path,
                "http_status": 401
            }
        ) 