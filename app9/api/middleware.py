import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from typing import Callable, Dict, List, Optional

from ..config import Config
from ..utils.logger import get_logger

# Configuração do logger
logger = get_logger(nome_app="middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para registrar logs de requisições e respostas.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Registrar início da requisição
        start_time = time.time()
        
        # Obter informações da requisição
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Registrar requisição
        logger.info(f"Requisição iniciada: {method} {url} de {client_host}")
        
        # Processar requisição
        try:
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Registrar resposta
            logger.info(
                f"Requisição concluída: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Tempo: {process_time:.4f}s"
            )
            
            # Adicionar header com tempo de processamento
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # Registrar erro
            logger.error(f"Erro ao processar requisição: {method} {url} - {str(e)}")
            raise
        
class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticação via API Key.
    """
    
    def __init__(self, app, api_key: str, exclude_paths: List[str] = None):
        super().__init__(app)
        self.api_key = api_key
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar se o path está excluído da autenticação
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Verificar API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.api_key:
            return Response(
                content='{"detail": "API Key inválida ou ausente"}',
                status_code=401,
                media_type="application/json"
            )
        
        return await call_next(request)

def setup_middlewares(app):
    """
    Configura os middlewares da aplicação.
    
    Args:
        app: Aplicação FastAPI
    """
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adicionar middleware de logging
    app.add_middleware(LoggingMiddleware)
    
    # Adicionar middleware de API Key se configurado
    if Config.API_KEY_ENABLED and Config.API_KEY:
        app.add_middleware(
            APIKeyMiddleware,
            api_key=Config.API_KEY,
            exclude_paths=["/docs", "/redoc", "/openapi.json", "/"]
        )
    
    logger.info("Middlewares configurados com sucesso") 