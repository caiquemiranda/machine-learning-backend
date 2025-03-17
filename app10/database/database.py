#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..config import Config
from ..utils.logger import app_logger

# Criação do diretório de dados se não existir
os.makedirs('data', exist_ok=True)

# URL de conexão com o banco de dados
SQLALCHEMY_DATABASE_URL = Config.DATABASE_URL

# Criação do engine do SQLAlchemy
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verificar conexão antes de usar
        pool_recycle=3600,   # Reciclar conexões a cada hora
        pool_size=10,        # Tamanho do pool de conexões
        max_overflow=20      # Conexões extras quando o pool estiver cheio
    )
    app_logger.info(f"Conexão com o banco de dados estabelecida: {SQLALCHEMY_DATABASE_URL}")
except Exception as e:
    app_logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
    raise

# Sessão do SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

# Inicialização do banco de dados
def init_db():
    """
    Inicializa o banco de dados criando as tabelas definidas nos modelos.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    from .models import Base
    
    try:
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        app_logger.info("Tabelas do banco de dados criadas com sucesso")
        return True
    except SQLAlchemyError as e:
        app_logger.error(f"Erro ao criar tabelas do banco de dados: {str(e)}")
        return False

# Verificar status do banco de dados
def check_db_status():
    """
    Verifica o status da conexão com o banco de dados.
    
    Returns:
        str: Status da conexão ("ok" ou mensagem de erro)
    """
    try:
        # Tentar executar uma consulta simples
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return "ok"
    except SQLAlchemyError as e:
        app_logger.error(f"Erro ao verificar status do banco de dados: {str(e)}")
        return str(e) 