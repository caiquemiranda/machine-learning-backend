#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class AlgoritmoEnum(str, Enum):
    """
    Enum para os algoritmos de ML suportados.
    """
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    DECISION_TREE = "decision_tree"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVR = "svr"
    ELASTIC_NET = "elastic_net"


class StatusTarefaEnum(str, Enum):
    """
    Enum para os status possíveis de uma tarefa.
    """
    PENDENTE = "pendente"
    EM_PROGRESSO = "em_progresso"
    CONCLUIDA = "concluida"
    FALHA = "falha"


class DadosEntradaBase(BaseModel):
    """
    Modelo base para dados de entrada.
    """
    area: float = Field(..., description="Área do imóvel em metros quadrados")
    quartos: int = Field(..., description="Número de quartos")
    banheiros: int = Field(..., description="Número de banheiros")
    garagem: int = Field(..., description="Vagas de garagem")
    idade: int = Field(..., description="Idade do imóvel em anos")
    
    @validator('area')
    def area_deve_ser_positiva(cls, v):
        if v <= 0:
            raise ValueError('A área deve ser um valor positivo')
        return v
    
    @validator('quartos', 'banheiros', 'garagem', 'idade')
    def valores_devem_ser_positivos(cls, v):
        if v < 0:
            raise ValueError('Os valores devem ser maiores ou iguais a zero')
        return v


class DadosEntradaPrevisao(DadosEntradaBase):
    """
    Modelo para dados de entrada para previsão.
    """
    pass


class DadosEntradaTreinamento(BaseModel):
    """
    Modelo para dados de entrada para treinamento.
    """
    dados: List[Dict[str, Any]] = Field(..., description="Lista de registros para treinamento")
    algoritmo: AlgoritmoEnum = Field(
        default=AlgoritmoEnum.LINEAR_REGRESSION,
        description="Algoritmo a ser utilizado no treinamento"
    )
    async_task: bool = Field(
        default=True,
        description="Indica se o treinamento deve ser executado de forma assíncrona"
    )


class ResultadoPrevisao(BaseModel):
    """
    Modelo para resultado de previsão.
    """
    preco_previsto: float = Field(..., description="Preço previsto para o imóvel")
    confianca: Optional[float] = Field(None, description="Nível de confiança da previsão")
    modelo_usado: str = Field(..., description="Nome do modelo utilizado na previsão")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da previsão")


class ResultadoTreinamento(BaseModel):
    """
    Modelo para resultado de treinamento.
    """
    algoritmo: str = Field(..., description="Algoritmo utilizado no treinamento")
    mae: float = Field(..., description="Mean Absolute Error")
    mse: float = Field(..., description="Mean Squared Error")
    r2: float = Field(..., description="R² Score")
    tempo_treinamento: float = Field(..., description="Tempo de treinamento em segundos")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do treinamento")


class StatusTarefa(BaseModel):
    """
    Modelo para status de uma tarefa assíncrona.
    """
    task_id: str = Field(..., description="ID da tarefa")
    status: StatusTarefaEnum = Field(..., description="Status atual da tarefa")
    resultado: Optional[Dict[str, Any]] = Field(None, description="Resultado da tarefa, se concluída")
    erro: Optional[str] = Field(None, description="Mensagem de erro, se falhou")
    timestamp_inicio: datetime = Field(..., description="Timestamp de início da tarefa")
    timestamp_atualizacao: datetime = Field(..., description="Timestamp da última atualização")


class StatusAPI(BaseModel):
    """
    Modelo para status da API.
    """
    versao: str = Field(..., description="Versão da API")
    status: str = Field(..., description="Status da API")
    modelo_carregado: bool = Field(..., description="Indica se o modelo está carregado")
    ultima_atualizacao_modelo: Optional[datetime] = Field(None, description="Timestamp da última atualização do modelo")
    algoritmo_atual: Optional[str] = Field(None, description="Algoritmo atual do modelo")
    metricas: Optional[Dict[str, float]] = Field(None, description="Métricas do modelo atual")
    status_celery: Dict[str, Any] = Field(..., description="Status do Celery")
    status_banco_dados: str = Field(..., description="Status do banco de dados")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da consulta de status") 