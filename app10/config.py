#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env se existir
load_dotenv()

class Config(BaseSettings):
    """
    Configurações centralizadas da aplicação usando Pydantic.
    Permite carregar configurações de variáveis de ambiente ou valores padrão.
    """
    
    # Configurações da API
    API_TITLE: str = "API de Previsão de Preços de Imóveis"
    API_DESCRIPTION: str = "API para previsão de preços de imóveis com arquitetura containerizada e CI/CD"
    API_VERSION: str = "10.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Configurações de autenticação
    API_KEY_ENABLED: bool = Field(default=True, env="API_KEY_ENABLED")
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    
    # Configurações de CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Configurações de banco de dados
    DB_HOST: str = Field(default="db", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="app10", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    
    # URL de conexão com o banco de dados
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Configurações de diretórios
    LOGS_DIR: str = Field(default="logs", env="LOGS_DIR")
    MODELS_DIR: str = Field(default="modelos", env="MODELS_DIR")
    
    # Configurações de ML
    DEFAULT_ALGORITHM: str = Field(default="linear_regression", env="DEFAULT_ALGORITHM")
    MODEL_FILE: str = Field(default="modelo_preco_imovel.joblib", env="MODEL_FILE")
    
    # Configurações do Celery
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Configurações de logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Configurações Sentry (monitoramento de erros)
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = Field(default="development", env="SENTRY_ENVIRONMENT")
    
    # Configurações de métricas Prometheus
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # Validação de API KEY
    @validator("API_KEY")
    def validate_api_key(cls, v, values):
        if values.get("API_KEY_ENABLED", False) and not v:
            raise ValueError("API_KEY deve ser fornecida quando API_KEY_ENABLED é True")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância única das configurações
config = Config()

# Para compatibilidade com código existente
settings = config 