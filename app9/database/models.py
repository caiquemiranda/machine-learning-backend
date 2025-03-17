#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, JSON, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class StatusTarefa(str, enum.Enum):
    """Enum para representar os possíveis status de uma tarefa assíncrona"""
    PENDENTE = "PENDENTE"
    EM_PROGRESSO = "EM_PROGRESSO"
    CONCLUIDO = "CONCLUIDO"
    FALHA = "FALHA"
    CANCELADO = "CANCELADO"

class TipoTarefa(str, enum.Enum):
    """Enum para representar os tipos de tarefas assíncronas"""
    TREINAMENTO = "TREINAMENTO"
    PREVISAO = "PREVISAO"
    PREVISAO_LOTE = "PREVISAO_LOTE"
    OUTRO = "OUTRO"

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
    
    # Relacionamentos
    dados_treinamento = relationship("DadoTreinamento", back_populates="modelo")
    previsoes = relationship("Previsao", back_populates="modelo")
    
    # Se foi treinado via tarefa assíncrona
    task_id = Column(String, nullable=True)
    
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
            "ativo": self.ativo,
            "task_id": self.task_id
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
    
    # Se foi uma previsão via tarefa assíncrona
    task_id = Column(String, nullable=True)
    
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
            "faixa_confianca": [self.intervalo_confianca_min, self.intervalo_confianca_max],
            "task_id": self.task_id
        }

class TarefaAssincrona(Base):
    """Modelo para rastrear tarefas assíncronas executadas pelo Celery"""
    __tablename__ = "tarefas_assincronas"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)
    tipo = Column(Enum(TipoTarefa), nullable=False)
    status = Column(Enum(StatusTarefa), default=StatusTarefa.PENDENTE, nullable=False)
    
    # Timestamps para rastreamento
    timestamp_criacao = Column(DateTime, default=datetime.now, nullable=False)
    timestamp_inicio = Column(DateTime, nullable=True)
    timestamp_fim = Column(DateTime, nullable=True)
    
    # Detalhes da tarefa
    descricao = Column(String(255), nullable=True)
    parametros = Column(JSON, nullable=True)
    resultado = Column(JSON, nullable=True)
    erro = Column(Text, nullable=True)
    
    # Relacionamentos
    modelo_id = Column(Integer, ForeignKey("modelos_info.id"), nullable=True)
    modelo = relationship("ModeloInfo", back_populates="tarefas")
    previsoes = relationship("Previsao", back_populates="tarefa")
    
    def __repr__(self):
        return f"<Tarefa {self.task_id} - {self.tipo} - {self.status}>"
    
    @property
    def duracao(self):
        """Calcula a duração da tarefa em segundos"""
        if self.timestamp_inicio and self.timestamp_fim:
            return (self.timestamp_fim - self.timestamp_inicio).total_seconds()
        return None
    
    @property
    def tempo_espera(self):
        """Calcula o tempo de espera antes do início da tarefa em segundos"""
        if self.timestamp_inicio:
            return (self.timestamp_inicio - self.timestamp_criacao).total_seconds()
        return None

class ModeloInfo(Base):
    """Modelo para armazenar informações sobre modelos de ML treinados"""
    __tablename__ = "modelos_info"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    algoritmo = Column(String(50), nullable=False)
    versao = Column(String(20), nullable=False)
    
    # Caminho para o arquivo do modelo salvo
    arquivo_modelo = Column(String(255), nullable=False)
    
    # Métricas de desempenho
    r2_score = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    
    # Informações sobre o treinamento
    timestamp_treinamento = Column(DateTime, default=datetime.now, nullable=False)
    tamanho_dataset = Column(Integer, nullable=True)
    features = Column(JSON, nullable=True)
    hiperparametros = Column(JSON, nullable=True)
    
    # Status do modelo
    ativo = Column(Boolean, default=False)
    
    # Relacionamentos
    tarefas = relationship("TarefaAssincrona", back_populates="modelo")
    previsoes = relationship("Previsao", back_populates="modelo")
    
    def __repr__(self):
        return f"<Modelo {self.nome} - {self.algoritmo} v{self.versao}>"

class Previsao(Base):
    """Modelo para armazenar previsões realizadas"""
    __tablename__ = "previsoes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificadores
    request_id = Column(String(50), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # Dados de entrada
    dados_entrada = Column(JSON, nullable=True)
    
    # Resultado da previsão
    valor_previsto = Column(Float, nullable=False)
    intervalo_confianca_min = Column(Float, nullable=True)
    intervalo_confianca_max = Column(Float, nullable=True)
    
    # Relacionamentos
    modelo_id = Column(Integer, ForeignKey("modelos_info.id"), nullable=False)
    modelo = relationship("ModeloInfo", back_populates="previsoes")
    
    tarefa_id = Column(Integer, ForeignKey("tarefas_assincronas.id"), nullable=True)
    tarefa = relationship("TarefaAssincrona", back_populates="previsoes")
    
    def __repr__(self):
        return f"<Previsao {self.id} - Valor: {self.valor_previsto}>" 