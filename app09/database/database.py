#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..config import Config

# Configuração do logger
logger = logging.getLogger(__name__)

# Criação do diretório de banco de dados se não existir
os.makedirs(Config.DB_DIR, exist_ok=True)

# URL de conexão com o banco de dados
SQLALCHEMY_DATABASE_URL = Config.DATABASE_URL

# Criação do engine do SQLAlchemy
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
        echo=False  # Definir como True para ver as queries SQL
    )
    logger.info(f"Conexão com o banco de dados estabelecida: {SQLALCHEMY_DATABASE_URL}")
except Exception as e:
    logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
    raise

# Sessão do SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos declarativos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    """
    Função geradora para obter uma sessão do banco de dados.
    Garante que a sessão seja fechada após o uso.
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para inicializar o banco de dados
def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas definidas.
    """
    try:
        # Importa os modelos para garantir que eles sejam registrados
        from .models import StatusTarefa, ModeloInfo, Previsao
        
        # Cria as tabelas
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas do banco de dados criadas com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")
        return False 