#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.pool import StaticPool

# Configuração de logging
logger = logging.getLogger('imoveis-api.database')

# Diretório para o banco de dados
DB_DIR = 'database'
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Conexão com o banco de dados
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'imoveis.db')}"

# Configuração do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite
    poolclass=StaticPool,  # Mantém a conexão aberta para uso em threads
    echo=False,  # Define como True para mostrar o SQL gerado
)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sessão para a aplicação
db_session = scoped_session(SessionLocal)

# Classe base para os modelos
Base = declarative_base()
Base.query = db_session.query_property()

# Função para obter uma sessão do banco de dados
def get_db():
    """
    Obtém uma nova sessão do banco de dados.
    Para ser utilizada como dependência no FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos ORM
class ModeloTreinamento(Base):
    """
    Modelo de dados para registros de treinamento.
    """
    __tablename__ = "modelos_treinamento"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    num_amostras = Column(Integer)
    r2_score = Column(Float)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    coeficientes = Column(JSON)  # Armazena os coeficientes como JSON
    features_utilizadas = Column(JSON)  # Lista de features como JSON
    
    # Relacionamento com dados de treinamento
    dados_treinamento = relationship("DadoTreinamento", back_populates="treinamento", cascade="all, delete-orphan")
    
    def as_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "num_amostras": self.num_amostras,
            "r2_score": self.r2_score,
            "rmse": self.rmse,
            "mae": self.mae,
            "coeficientes": self.coeficientes,
            "features_utilizadas": self.features_utilizadas
        }


class DadoTreinamento(Base):
    """
    Modelo de dados para os dados utilizados no treinamento.
    """
    __tablename__ = "dados_treinamento"

    id = Column(Integer, primary_key=True, index=True)
    treinamento_id = Column(Integer, ForeignKey("modelos_treinamento.id"))
    area = Column(Float)
    quartos = Column(Integer, nullable=True)
    banheiros = Column(Integer, nullable=True)
    idade_imovel = Column(Integer, nullable=True)
    preco = Column(Float)
    
    # Relacionamento com o modelo de treinamento
    treinamento = relationship("ModeloTreinamento", back_populates="dados_treinamento")
    
    def as_dict(self):
        return {
            "id": self.id,
            "area": self.area,
            "quartos": self.quartos,
            "banheiros": self.banheiros,
            "idade_imovel": self.idade_imovel,
            "preco": self.preco
        }


class Previsao(Base):
    """
    Modelo de dados para registros de previsões.
    """
    __tablename__ = "previsoes"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    area = Column(Float)
    quartos = Column(Integer, nullable=True)
    banheiros = Column(Integer, nullable=True)
    idade_imovel = Column(Integer, nullable=True)
    preco_previsto = Column(Float)
    faixa_inferior = Column(Float)
    faixa_superior = Column(Float)
    
    def as_dict(self):
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "input": {
                "area": self.area,
                "quartos": self.quartos,
                "banheiros": self.banheiros,
                "idade_imovel": self.idade_imovel
            },
            "preco_previsto": self.preco_previsto,
            "faixa_confianca": (self.faixa_inferior, self.faixa_superior)
        }


def criar_tabelas():
    """
    Cria todas as tabelas no banco de dados se ainda não existirem.
    """
    logger.info("Criando tabelas no banco de dados...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise 