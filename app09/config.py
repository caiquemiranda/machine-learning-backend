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
    API_DESCRIPTION: str = "API para previsão de preços de imóveis com suporte para processamento assíncrono"
    API_VERSION: str = "9.0.0"
    DEBUG: bool = Field(default=True, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Configurações de autenticação
    API_KEY_ENABLED: bool = Field(default=False, env="API_KEY_ENABLED")
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    
    # Configurações de CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Configurações de banco de dados
    DB_DIR: str = Field(default="data", env="DB_DIR")
    DB_NAME: str = Field(default="app9.db", env="DB_NAME")
    
    # Configurações de diretórios
    LOGS_DIR: str = Field(default="logs", env="LOGS_DIR")
    MODELS_DIR: str = Field(default="modelos", env="MODELS_DIR")
    
    # Configurações de ML
    DEFAULT_ALGORITHM: str = Field(default="linear_regression", env="DEFAULT_ALGORITHM")
    MODEL_FILE: str = Field(default="modelo_preco_imovel.joblib", env="MODEL_FILE")
    
    # Configurações do Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # URLs externas
    FLOWER_URL: str = Field(default="http://localhost:5555", env="FLOWER_URL")
    
    # Propriedades calculadas
    @property
    def DATABASE_URL(self) -> str:
        """URL de conexão com o banco de dados SQLite"""
        os.makedirs(self.DB_DIR, exist_ok=True)
        return f"sqlite:///{os.path.join(self.DB_DIR, self.DB_NAME)}"
    
    @property
    def REDIS_URL(self) -> str:
        """URL de conexão com o Redis"""
        return self.CELERY_BROKER_URL
    
    @property
    def MODEL_PATH(self) -> str:
        """Caminho completo para o arquivo do modelo"""
        return os.path.join(self.MODELS_DIR, self.MODEL_FILE)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instância única das configurações
config = Config()

# Para compatibilidade com código existente
settings = config 