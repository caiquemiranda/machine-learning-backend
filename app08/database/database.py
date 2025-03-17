#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from .models import Base

# Configuração do banco de dados
DATABASE_DIR = 'database'
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'imobiliaria.db')}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Fornece uma sessão de banco de dados para operações de banco de dados.
    É usado como uma dependência na aplicação FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def criar_tabelas():
    """
    Cria todas as tabelas definidas em models.py se elas ainda não existirem.
    """
    Base.metadata.create_all(bind=engine) 