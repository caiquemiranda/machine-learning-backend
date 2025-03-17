#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from datetime import datetime

class ProcessamentoEnum(str, Enum):
    """Tipo de processamento disponível"""
    SINCRONO = "sincrono"
    ASSINCRONO = "assincrono"

class AlgoritmoEnum(str, Enum):
    """Algoritmos de ML suportados"""
    LINEAR_REGRESSION = "linear_regression"
    RIDGE = "ridge"
    LASSO = "lasso"
    ELASTIC_NET = "elastic_net"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVR = "svr"

class StatusTarefaEnum(str, Enum):
    """Status possíveis para tarefas assíncronas"""
    PENDENTE = "PENDENTE"
    EM_PROGRESSO = "EM_PROGRESSO"
    CONCLUIDO = "CONCLUIDO"
    FALHA = "FALHA"
    CANCELADO = "CANCELADO"

class TipoTarefaEnum(str, Enum):
    """Tipos de tarefas assíncronas"""
    TREINAMENTO = "TREINAMENTO"
    PREVISAO = "PREVISAO"
    PREVISAO_LOTE = "PREVISAO_LOTE"
    OUTRO = "OUTRO"

class PrevisaoInput(BaseModel):
    """
    Esquema para entrada de previsão
    """
    area: float = Field(..., description="Área do imóvel em metros quadrados", gt=0)
    quartos: Optional[int] = Field(None, description="Número de quartos", ge=0)
    banheiros: Optional[int] = Field(None, description="Número de banheiros", ge=0)
    idade_imovel: Optional[int] = Field(None, description="Idade do imóvel em anos", ge=0)
    processamento: ProcessamentoEnum = Field(
        default=ProcessamentoEnum.SINCRONO, 
        description="Tipo de processamento: síncrono ou assíncrono"
    )
    
    @validator('area')
    def area_deve_ser_razoavel(cls, v):
        if v > 10000:
            raise ValueError("Área muito grande. O valor deve ser menor que 10.000 m²")
        return v
    
    @validator('quartos', 'banheiros')
    def valores_devem_ser_razoaveis(cls, v):
        if v is not None and v > 20:
            raise ValueError("Valor muito alto. O valor deve ser menor que 20")
        return v

    @root_validator
    def verificar_valores(cls, values):
        # Lógica mais complexa de validação
        area = values.get('area')
        quartos = values.get('quartos')
        
        if area and quartos and area < quartos * 8:
            raise ValueError(
                "A área é muito pequena para o número de quartos. "
                "Considere pelo menos 8m² por quarto."
            )
        return values

class TreinamentoInput(BaseModel):
    """
    Esquema para entrada de treinamento
    """
    features: List[Dict[str, Any]] = Field(..., description="Lista de características dos imóveis")
    precos: List[float] = Field(..., description="Lista de preços correspondentes aos imóveis")
    algoritmo: Optional[str] = Field("linear_regression", description="Algoritmo de ML a ser utilizado")
    hiperparametros: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Hiperparâmetros para o algoritmo")
    processamento: ProcessamentoEnum = Field(
        default=ProcessamentoEnum.SINCRONO, 
        description="Tipo de processamento: síncrono ou assíncrono"
    )
    
    @validator('features')
    def validar_features(cls, v):
        if not v:
            raise ValueError("Ao menos um imóvel deve ser fornecido")
        
        # Verifica se todos os dicionários têm a chave 'area'
        for i, item in enumerate(v):
            if 'area' not in item:
                raise ValueError(f"O imóvel na posição {i} não possui o campo 'area' (obrigatório)")
            
            # Validação dos valores
            if item['area'] <= 0:
                raise ValueError(f"Área do imóvel na posição {i} deve ser maior que zero")
                
            # Validação dos quartos
            if 'quartos' in item and (not isinstance(item['quartos'], (int, float)) or item['quartos'] < 0):
                raise ValueError(f"Número de quartos do imóvel na posição {i} inválido")
                
            # Validação dos banheiros
            if 'banheiros' in item and (not isinstance(item['banheiros'], (int, float)) or item['banheiros'] < 0):
                raise ValueError(f"Número de banheiros do imóvel na posição {i} inválido")
                
            # Validação da idade
            if 'idade_imovel' in item and (not isinstance(item['idade_imovel'], (int, float)) or item['idade_imovel'] < 0):
                raise ValueError(f"Idade do imóvel na posição {i} inválida")
            
        return v
        
    @validator('precos')
    def validar_precos(cls, v, values):
        if 'features' not in values:
            raise ValueError("Dados das características dos imóveis não fornecidos")
            
        if len(v) != len(values['features']):
            raise ValueError(
                f"Número de preços ({len(v)}) não corresponde ao número de imóveis "
                f"({len(values['features'])})"
            )
            
        # Verifica se preços são positivos
        for i, preco in enumerate(v):
            if preco <= 0:
                raise ValueError(f"Preço na posição {i} deve ser maior que zero")
                
        return v

class PrevisaoOutput(BaseModel):
    """
    Esquema para saída de previsão
    """
    request_id: str
    timestamp: str
    area: float
    quartos: Optional[int] = None
    banheiros: Optional[int] = None
    idade_imovel: Optional[int] = None
    preco_previsto: float
    faixa_confianca: Tuple[float, float]
    task_id: Optional[str] = None

class TarefaResponse(BaseModel):
    """Resposta para criação de tarefa assíncrona"""
    task_id: str = Field(..., description="ID da tarefa")
    tipo: TipoTarefaEnum = Field(..., description="Tipo da tarefa")
    status: StatusTarefaEnum = Field(..., description="Status atual da tarefa")
    timestamp_criacao: datetime = Field(..., description="Timestamp de criação da tarefa")
    url_status: str = Field(..., description="URL para verificar o status da tarefa")

class StatusTarefaResponse(BaseModel):
    """Resposta para consulta de status de tarefa"""
    task_id: str = Field(..., description="ID da tarefa")
    tipo: TipoTarefaEnum = Field(..., description="Tipo da tarefa")
    status: StatusTarefaEnum = Field(..., description="Status atual da tarefa")
    timestamp_criacao: datetime = Field(..., description="Timestamp de criação da tarefa")
    timestamp_inicio: Optional[datetime] = Field(None, description="Timestamp de início da tarefa")
    timestamp_fim: Optional[datetime] = Field(None, description="Timestamp de conclusão da tarefa")
    resultado: Optional[Dict[str, Any]] = Field(None, description="Resultado da tarefa (se concluída)")
    erro: Optional[str] = Field(None, description="Mensagem de erro (se falhou)")
    duracao: Optional[float] = Field(None, description="Duração da tarefa em segundos (se concluída)")

class StatusOutput(BaseModel):
    """
    Esquema para saída do status da API
    """
    modelo_salvo: bool
    modelo_carregado: bool
    algoritmo_atual: Optional[str] = None
    features_suportadas: List[str]
    numero_amostras_treinamento: Optional[int] = None
    metricas_modelo: Optional[Dict[str, float]] = None
    estatisticas_api: Dict[str, Any]
    metricas_banco_dados: Dict[str, Any]
    tarefas_ativas: Dict[str, int]
    suporte_assincrono: bool = True

class ErrorResponse(BaseModel):
    """Resposta para erros"""
    detail: str = Field(..., description="Mensagem de erro")
    status_code: int = Field(..., description="Código de status HTTP")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")

class HistoricoPrevisao(BaseModel):
    """
    Esquema para itens do histórico de previsão
    """
    request_id: str
    timestamp: str
    input: Dict[str, Any]
    preco_previsto: float
    faixa_confianca: Tuple[float, float]
    task_id: Optional[str] = None

class ModeloDetail(BaseModel):
    """
    Detalhes de um modelo treinado
    """
    id: int
    request_id: str
    timestamp: str
    algoritmo: str
    num_amostras: int
    r2_score: float
    rmse: Optional[float] = None
    mae: Optional[float] = None
    coeficientes: Dict[str, float]
    features_utilizadas: List[str]
    hiperparametros: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None

class DadosImovel(BaseModel):
    """Dados de entrada para previsão de preço de imóvel"""
    area: float = Field(..., gt=0, description="Área do imóvel em metros quadrados")
    quartos: int = Field(..., ge=0, description="Número de quartos")
    banheiros: int = Field(..., ge=0, description="Número de banheiros")
    idade_imovel: float = Field(..., ge=0, description="Idade do imóvel em anos")

class DadosImovelOpcional(BaseModel):
    """Dados de entrada para previsão de preço de imóvel com campos opcionais"""
    area: Optional[float] = Field(None, gt=0, description="Área do imóvel em metros quadrados")
    quartos: Optional[int] = Field(None, ge=0, description="Número de quartos")
    banheiros: Optional[int] = Field(None, ge=0, description="Número de banheiros")
    idade_imovel: Optional[float] = Field(None, ge=0, description="Idade do imóvel em anos")

class DadosTreinamento(BaseModel):
    """Dados para treinamento do modelo"""
    imoveis: List[Dict[str, Any]] = Field(..., min_items=1, description="Lista de imóveis para treinamento")
    algoritmo: AlgoritmoEnum = Field(AlgoritmoEnum.LINEAR_REGRESSION, description="Algoritmo a ser utilizado")
    hiperparametros: Optional[Dict[str, Any]] = Field(None, description="Hiperparâmetros para o algoritmo")
    assincrono: bool = Field(False, description="Se o treinamento deve ser executado de forma assíncrona")

class PrevisaoRequest(BaseModel):
    """Requisição para previsão de preço"""
    imovel: DadosImovel
    assincrono: bool = Field(False, description="Se a previsão deve ser executada de forma assíncrona")

class PrevisaoLoteRequest(BaseModel):
    """Requisição para previsão de preço em lote"""
    imoveis: List[DadosImovel] = Field(..., min_items=1, description="Lista de imóveis para previsão")
    assincrono: bool = Field(True, description="Se a previsão deve ser executada de forma assíncrona")

class IntervaloConfianca(BaseModel):
    """Intervalo de confiança para previsão"""
    min: float = Field(..., description="Valor mínimo do intervalo de confiança")
    max: float = Field(..., description="Valor máximo do intervalo de confiança")

class PrevisaoResponse(BaseModel):
    """Resposta para previsão de preço"""
    valor_previsto: float = Field(..., description="Valor previsto para o imóvel")
    intervalo_confianca: IntervaloConfianca = Field(..., description="Intervalo de confiança da previsão")
    algoritmo: str = Field(..., description="Algoritmo utilizado na previsão")
    timestamp: datetime = Field(..., description="Timestamp da previsão")

class PrevisaoLoteResponse(BaseModel):
    """Resposta para previsão de preço em lote"""
    previsoes: List[Dict[str, Any]] = Field(..., description="Lista de previsões")
    total: int = Field(..., description="Total de previsões realizadas")
    algoritmo: str = Field(..., description="Algoritmo utilizado nas previsões")
    timestamp: datetime = Field(..., description="Timestamp das previsões")

class MetricasModelo(BaseModel):
    """Métricas de desempenho do modelo"""
    r2_score: float = Field(..., description="Coeficiente de determinação (R²)")
    mae: float = Field(..., description="Erro absoluto médio")
    mse: float = Field(..., description="Erro quadrático médio")
    rmse: float = Field(..., description="Raiz do erro quadrático médio")
    tamanho_dataset: int = Field(..., description="Tamanho total do dataset")
    tamanho_treino: int = Field(..., description="Tamanho do conjunto de treino")
    tamanho_teste: int = Field(..., description="Tamanho do conjunto de teste")

class TreinamentoResponse(BaseModel):
    """Resposta para treinamento do modelo"""
    algoritmo: str = Field(..., description="Algoritmo utilizado no treinamento")
    metricas: MetricasModelo = Field(..., description="Métricas de desempenho do modelo")
    timestamp: datetime = Field(..., description="Timestamp do treinamento")

class InfoModelo(BaseModel):
    """Informações sobre o modelo atual"""
    modelo_treinado: bool = Field(..., description="Se o modelo está treinado")
    algoritmo: Optional[str] = Field(None, description="Algoritmo utilizado no modelo")
    features: Optional[List[str]] = Field(None, description="Features utilizadas no modelo")
    data_treinamento: Optional[str] = Field(None, description="Data do último treinamento")
    metricas: Optional[Dict[str, Any]] = Field(None, description="Métricas do modelo")
    total_previsoes: int = Field(0, description="Total de previsões realizadas")

class ListaTarefasResponse(BaseModel):
    """Resposta para listagem de tarefas"""
    tarefas: List[StatusTarefaResponse] = Field(..., description="Lista de tarefas")
    total: int = Field(..., description="Total de tarefas")
    pendentes: int = Field(..., description="Total de tarefas pendentes")
    em_progresso: int = Field(..., description="Total de tarefas em progresso")
    concluidas: int = Field(..., description="Total de tarefas concluídas")
    falhas: int = Field(..., description="Total de tarefas com falha")

class WorkerInfo(BaseModel):
    """Informações sobre um worker Celery"""
    id: str = Field(..., description="ID do worker")
    status: str = Field(..., description="Status do worker")
    tarefas_processadas: int = Field(..., description="Total de tarefas processadas")
    tarefas_ativas: int = Field(..., description="Total de tarefas ativas")

class CeleryStatusResponse(BaseModel):
    """Resposta para status do Celery"""
    status: str = Field(..., description="Status geral do Celery")
    workers: List[WorkerInfo] = Field(..., description="Lista de workers")
    filas: Dict[str, int] = Field(..., description="Filas e quantidade de tarefas")
    total_workers: int = Field(..., description="Total de workers")
    total_tarefas_ativas: int = Field(..., description="Total de tarefas ativas")

class ErrorResponse(BaseModel):
    """
    Esquema para respostas de erro
    """
    request_id: str
    timestamp: str
    error: str
    detail: str
    path: str
    http_status: int

class HistoricoPrevisao(BaseModel):
    """
    Esquema para itens do histórico de previsão
    """
    request_id: str
    timestamp: str
    input: Dict[str, Any]
    preco_previsto: float
    faixa_confianca: Tuple[float, float]
    task_id: Optional[str] = None

class ModeloDetail(BaseModel):
    """
    Detalhes de um modelo treinado
    """
    id: int
    request_id: str
    timestamp: str
    algoritmo: str
    num_amostras: int
    r2_score: float
    rmse: Optional[float] = None
    mae: Optional[float] = None
    coeficientes: Dict[str, float]
    features_utilizadas: List[str]
    hiperparametros: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None

class DadosImovel(BaseModel):
    """Dados de entrada para previsão de preço de imóvel"""
    area: float = Field(..., gt=0, description="Área do imóvel em metros quadrados")
    quartos: int = Field(..., ge=0, description="Número de quartos")
    banheiros: int = Field(..., ge=0, description="Número de banheiros")
    idade_imovel: float = Field(..., ge=0, description="Idade do imóvel em anos")

class DadosImovelOpcional(BaseModel):
    """Dados de entrada para previsão de preço de imóvel com campos opcionais"""
    area: Optional[float] = Field(None, gt=0, description="Área do imóvel em metros quadrados")
    quartos: Optional[int] = Field(None, ge=0, description="Número de quartos")
    banheiros: Optional[int] = Field(None, ge=0, description="Número de banheiros")
    idade_imovel: Optional[float] = Field(None, ge=0, description="Idade do imóvel em anos")

class DadosTreinamento(BaseModel):
    """Dados para treinamento do modelo"""
    imoveis: List[Dict[str, Any]] = Field(..., min_items=1, description="Lista de imóveis para treinamento")
    algoritmo: AlgoritmoEnum = Field(AlgoritmoEnum.LINEAR_REGRESSION, description="Algoritmo a ser utilizado")
    hiperparametros: Optional[Dict[str, Any]] = Field(None, description="Hiperparâmetros para o algoritmo")
    assincrono: bool = Field(False, description="Se o treinamento deve ser executado de forma assíncrona")

class PrevisaoRequest(BaseModel):
    """Requisição para previsão de preço"""
    imovel: DadosImovel
    assincrono: bool = Field(False, description="Se a previsão deve ser executada de forma assíncrona")

class PrevisaoLoteRequest(BaseModel):
    """Requisição para previsão de preço em lote"""
    imoveis: List[DadosImovel] = Field(..., min_items=1, description="Lista de imóveis para previsão")
    assincrono: bool = Field(True, description="Se a previsão deve ser executada de forma assíncrona")

class IntervaloConfianca(BaseModel):
    """Intervalo de confiança para previsão"""
    min: float = Field(..., description="Valor mínimo do intervalo de confiança")
    max: float = Field(..., description="Valor máximo do intervalo de confiança")

class PrevisaoResponse(BaseModel):
    """Resposta para previsão de preço"""
    valor_previsto: float = Field(..., description="Valor previsto para o imóvel")
    intervalo_confianca: IntervaloConfianca = Field(..., description="Intervalo de confiança da previsão")
    algoritmo: str = Field(..., description="Algoritmo utilizado na previsão")
    timestamp: datetime = Field(..., description="Timestamp da previsão")

class PrevisaoLoteResponse(BaseModel):
    """Resposta para previsão de preço em lote"""
    previsoes: List[Dict[str, Any]] = Field(..., description="Lista de previsões")
    total: int = Field(..., description="Total de previsões realizadas")
    algoritmo: str = Field(..., description="Algoritmo utilizado nas previsões")
    timestamp: datetime = Field(..., description="Timestamp das previsões")

class MetricasModelo(BaseModel):
    """Métricas de desempenho do modelo"""
    r2_score: float = Field(..., description="Coeficiente de determinação (R²)")
    mae: float = Field(..., description="Erro absoluto médio")
    mse: float = Field(..., description="Erro quadrático médio")
    rmse: float = Field(..., description="Raiz do erro quadrático médio")
    tamanho_dataset: int = Field(..., description="Tamanho total do dataset")
    tamanho_treino: int = Field(..., description="Tamanho do conjunto de treino")
    tamanho_teste: int = Field(..., description="Tamanho do conjunto de teste")

class TreinamentoResponse(BaseModel):
    """Resposta para treinamento do modelo"""
    algoritmo: str = Field(..., description="Algoritmo utilizado no treinamento")
    metricas: MetricasModelo = Field(..., description="Métricas de desempenho do modelo")
    timestamp: datetime = Field(..., description="Timestamp do treinamento")

class InfoModelo(BaseModel):
    """Informações sobre o modelo atual"""
    modelo_treinado: bool = Field(..., description="Se o modelo está treinado")
    algoritmo: Optional[str] = Field(None, description="Algoritmo utilizado no modelo")
    features: Optional[List[str]] = Field(None, description="Features utilizadas no modelo")
    data_treinamento: Optional[str] = Field(None, description="Data do último treinamento")
    metricas: Optional[Dict[str, Any]] = Field(None, description="Métricas do modelo")
    total_previsoes: int = Field(0, description="Total de previsões realizadas")

class ListaTarefasResponse(BaseModel):
    """Resposta para listagem de tarefas"""
    tarefas: List[StatusTarefaResponse] = Field(..., description="Lista de tarefas")
    total: int = Field(..., description="Total de tarefas")
    pendentes: int = Field(..., description="Total de tarefas pendentes")
    em_progresso: int = Field(..., description="Total de tarefas em progresso")
    concluidas: int = Field(..., description="Total de tarefas concluídas")
    falhas: int = Field(..., description="Total de tarefas com falha")

class WorkerInfo(BaseModel):
    """Informações sobre um worker Celery"""
    id: str = Field(..., description="ID do worker")
    status: str = Field(..., description="Status do worker")
    tarefas_processadas: int = Field(..., description="Total de tarefas processadas")
    tarefas_ativas: int = Field(..., description="Total de tarefas ativas")

class CeleryStatusResponse(BaseModel):
    """Resposta para status do Celery"""
    status: str = Field(..., description="Status geral do Celery")
    workers: List[WorkerInfo] = Field(..., description="Lista de workers")
    filas: Dict[str, int] = Field(..., description="Filas e quantidade de tarefas")
    total_workers: int = Field(..., description="Total de workers")
    total_tarefas_ativas: int = Field(..., description="Total de tarefas ativas")

class ErrorResponse(BaseModel):
    """Resposta para erros"""
    detail: str = Field(..., description="Mensagem de erro")
    status_code: int = Field(..., description="Código de status HTTP")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")

class StatusOutput(BaseModel):
    """Status da API"""
    status: str = "online"
    versao: str = "9.0.0"
    modelo_carregado: bool = False
    total_previsoes: int = 0
    total_treinamentos: int = 0
    suporte_assincrono: bool = True 