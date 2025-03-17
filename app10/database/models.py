#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class ModeloTreinado(Base):
    """
    Modelo para armazenar informações sobre modelos de ML treinados.
    """
    __tablename__ = "modelos_treinados"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    algoritmo = Column(String(50), nullable=False)
    versao = Column(String(20), nullable=False)
    arquivo = Column(String(255), nullable=False)
    metricas = Column(JSON, nullable=True)
    hiperparametros = Column(JSON, nullable=True)
    data_treinamento = Column(DateTime, default=datetime.datetime.utcnow)
    ativo = Column(Boolean, default=True)
    observacoes = Column(Text, nullable=True)


class Predicao(Base):
    """
    Modelo para armazenar histórico de predições realizadas.
    """
    __tablename__ = "predicoes"
    
    id = Column(Integer, primary_key=True, index=True)
    modelo_id = Column(Integer, nullable=False)
    dados_entrada = Column(JSON, nullable=False)
    resultado = Column(Float, nullable=False)
    confianca = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    duracao = Column(Float, nullable=True)  # Duração da predição em segundos


class Tarefa(Base):
    """
    Modelo para armazenar informações sobre tarefas assíncronas.
    """
    __tablename__ = "tarefas"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True, nullable=False)
    tipo = Column(String(50), nullable=False)  # 'treinamento' ou 'predicao'
    status = Column(String(20), nullable=False)  # 'pendente', 'em_progresso', 'concluida', 'falha'
    dados_entrada = Column(JSON, nullable=True)
    resultado = Column(JSON, nullable=True)
    erro = Column(Text, nullable=True)
    timestamp_inicio = Column(DateTime, default=datetime.datetime.utcnow)
    timestamp_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    duracao = Column(Float, nullable=True)  # Duração da tarefa em segundos


class Log(Base):
    """
    Modelo para armazenar logs da aplicação no banco de dados.
    """
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    nivel = Column(String(20), nullable=False)
    mensagem = Column(Text, nullable=False)
    origem = Column(String(100), nullable=True)
    detalhes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    trace_id = Column(String(32), nullable=True)
    span_id = Column(String(16), nullable=True) 