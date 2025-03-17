#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ModeloTreinamento(Base):
    __tablename__ = "modelos_treinamento"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    num_amostras = Column(Integer)
    r2_score = Column(Float)
    rmse = Column(Float)
    mae = Column(Float)
    coeficientes = Column(JSON)
    features_utilizadas = Column(JSON)
    algoritmo = Column(String, default="LinearRegression")
    hiperparametros = Column(JSON)
    ativo = Column(Boolean, default=True)
    
    dados_treinamento = relationship("DadoTreinamento", back_populates="modelo")
    previsoes = relationship("Previsao", back_populates="modelo")
    
    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "num_amostras": self.num_amostras,
            "r2_score": self.r2_score,
            "rmse": self.rmse,
            "mae": self.mae,
            "coeficientes": self.coeficientes,
            "features_utilizadas": self.features_utilizadas,
            "algoritmo": self.algoritmo,
            "hiperparametros": self.hiperparametros,
            "ativo": self.ativo
        }

class DadoTreinamento(Base):
    __tablename__ = "dados_treinamento"
    
    id = Column(Integer, primary_key=True, index=True)
    modelo_id = Column(Integer, ForeignKey("modelos_treinamento.id"))
    area = Column(Float)
    quartos = Column(Integer, nullable=True)
    banheiros = Column(Integer, nullable=True)
    idade_imovel = Column(Integer, nullable=True)
    preco = Column(Float)
    
    modelo = relationship("ModeloTreinamento", back_populates="dados_treinamento")
    
    def to_dict(self):
        return {
            "id": self.id,
            "modelo_id": self.modelo_id,
            "area": self.area,
            "quartos": self.quartos,
            "banheiros": self.banheiros,
            "idade_imovel": self.idade_imovel,
            "preco": self.preco
        }

class Previsao(Base):
    __tablename__ = "previsoes"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    modelo_id = Column(Integer, ForeignKey("modelos_treinamento.id"))
    timestamp = Column(DateTime, default=datetime.now)
    area = Column(Float)
    quartos = Column(Integer, nullable=True)
    banheiros = Column(Integer, nullable=True)
    idade_imovel = Column(Integer, nullable=True)
    preco_previsto = Column(Float)
    intervalo_confianca_min = Column(Float)
    intervalo_confianca_max = Column(Float)
    
    modelo = relationship("ModeloTreinamento", back_populates="previsoes")
    
    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "modelo_id": self.modelo_id,
            "timestamp": self.timestamp.isoformat(),
            "input": {
                "area": self.area,
                "quartos": self.quartos,
                "banheiros": self.banheiros,
                "idade_imovel": self.idade_imovel
            },
            "preco_previsto": self.preco_previsto,
            "faixa_confianca": [self.intervalo_confianca_min, self.intervalo_confianca_max]
        } 