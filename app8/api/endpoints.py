#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

import numpy as np
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from database.database import get_db
from database.models import ModeloTreinamento, DadoTreinamento, Previsao
from api.schemas import (
    PrevisaoInput, PrevisaoOutput, TreinamentoInput, 
    StatusOutput, HistoricoPrevisao, ModeloDetail, ErrorResponse
)

# Importação circular, não fazer no código real
# Aqui é apenas para demonstração
router = APIRouter()
ml_service = None  # Será injetado na inicialização
logger = None  # Será injetado na inicialização

# Contador e métricas de API
contador_requisicoes = {
    "total": 0,
    "previsoes": 0,
    "treinamentos": 0,
    "consultas": 0,
    "erros": 0
}

tempo_inicio = time.time()

def registrar_requisicao(tipo):
    """Registra uma requisição nas estatísticas"""
    contador_requisicoes["total"] += 1
    if tipo in contador_requisicoes:
        contador_requisicoes[tipo] += 1

def get_estatisticas():
    """Retorna estatísticas da API"""
    tempo_execucao = time.time() - tempo_inicio
    return {
        "requisicoes": contador_requisicoes,
        "tempo_execucao_segundos": tempo_execucao,
        "media_requisicoes_por_minuto": contador_requisicoes["total"] / (tempo_execucao / 60) if tempo_execucao > 0 else 0
    }

def preparar_dados_previsao(dados: PrevisaoInput, request: Request):
    """
    Prepara os dados para previsão.
    
    Args:
        dados: Dados de entrada validados
        request: Objeto da requisição
        
    Returns:
        Tuple com dados preparados, nomes de feature, dados originais e ID de request
    """
    logger.info(f"Preparando dados para previsão: {dados.dict()}")
    
    # Extrai os valores em um array numpy
    features = np.array([
        [
            dados.area,
            dados.quartos if dados.quartos is not None else np.nan,
            dados.banheiros if dados.banheiros is not None else np.nan,
            dados.idade_imovel if dados.idade_imovel is not None else np.nan
        ]
    ])
    
    feature_names = ['area', 'quartos', 'banheiros', 'idade_imovel']
    request_id = str(uuid.uuid4())
    
    return features, feature_names, dados.dict(), request_id

@router.get("/", tags=["info"])
def index():
    """Retorna informações básicas da API"""
    registrar_requisicao("consultas")
    return {
        "nome": "API de Previsão de Preços de Imóveis v8.0",
        "descricao": "Uma API para prever preços de imóveis com base em características",
        "status": "online",
        "documentacao": "/docs",
        "data": datetime.now().isoformat()
    }

@router.post("/treinar", response_model=Dict[str, Union[str, int, float]], tags=["modelo"])
async def treinar(
    dados: TreinamentoInput, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Treina o modelo de previsão com os dados fornecidos.
    
    Args:
        dados: Dados de treinamento
        request: Objeto da requisição
        db: Sessão do banco de dados
        
    Returns:
        Informações sobre o treinamento realizado
    """
    try:
        registrar_requisicao("treinamentos")
        logger.info(f"Iniciando treinamento com {len(dados.features)} amostras")
        
        # Extrair as features
        features_array = []
        for imovel in dados.features:
            feature = [
                imovel.get('area', 0),
                imovel.get('quartos', np.nan),
                imovel.get('banheiros', np.nan),
                imovel.get('idade_imovel', np.nan)
            ]
            features_array.append(feature)
        
        X = np.array(features_array)
        y = np.array(dados.precos)
        
        # Treinar o modelo
        resultados = ml_service.treinar(
            X, 
            y, 
            algoritmo=dados.algoritmo, 
            hiperparametros=dados.hiperparametros, 
            db=db
        )
        
        logger.info(f"Treinamento concluído com sucesso: R² = {resultados['r2_score']:.4f}")
        return resultados
    
    except Exception as e:
        contador_requisicoes["erros"] += 1
        logger.error(f"Erro no treinamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no treinamento: {str(e)}")

@router.post("/prever", response_model=PrevisaoOutput, tags=["modelo"])
async def prever(
    dados: PrevisaoInput,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Realiza previsão de preço para um imóvel.
    
    Args:
        dados: Características do imóvel
        request: Objeto da requisição
        db: Sessão do banco de dados
        
    Returns:
        Previsão de preço e intervalos de confiança
    """
    try:
        registrar_requisicao("previsoes")
        
        # Prepara os dados
        features, feature_names, dados_dict, request_id = preparar_dados_previsao(dados, request)
        
        # Realiza a previsão
        try:
            valor_previsto, intervalo_confianca = ml_service.prever(features)
        except ValueError as e:
            if "Modelo não treinado" in str(e):
                raise HTTPException(
                    status_code=400, 
                    detail="O modelo ainda não foi treinado. Envie dados de treinamento primeiro."
                )
            raise
        
        # Resultado da previsão
        resultado_previsao = valor_previsto[0]
        intervalo_min, intervalo_max = intervalo_confianca[0]
        
        # Registra no banco de dados
        modelo_atual = db.query(ModeloTreinamento).filter_by(ativo=True).order_by(desc("id")).first()
        
        if modelo_atual:
            previsao_db = Previsao(
                request_id=request_id,
                modelo_id=modelo_atual.id,
                timestamp=datetime.now(),
                area=dados.area,
                quartos=dados.quartos,
                banheiros=dados.banheiros,
                idade_imovel=dados.idade_imovel,
                preco_previsto=float(resultado_previsao),
                intervalo_confianca_min=float(intervalo_min),
                intervalo_confianca_max=float(intervalo_max)
            )
            db.add(previsao_db)
            db.commit()
        
        # Monta a resposta
        resposta = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "area": dados.area,
            "quartos": dados.quartos,
            "banheiros": dados.banheiros,
            "idade_imovel": dados.idade_imovel,
            "preco_previsto": float(resultado_previsao),
            "faixa_confianca": (float(intervalo_min), float(intervalo_max))
        }
        
        logger.info(f"Previsão realizada: {resposta['preco_previsto']:.2f}")
        return resposta
        
    except HTTPException:
        contador_requisicoes["erros"] += 1
        raise
    except Exception as e:
        contador_requisicoes["erros"] += 1
        logger.error(f"Erro na previsão: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")

@router.get("/previsoes", response_model=List[HistoricoPrevisao], tags=["historico"])
async def listar_previsoes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lista o histórico de previsões realizadas.
    
    Args:
        limit: Limite de resultados
        offset: Offset para paginação
        db: Sessão do banco de dados
        
    Returns:
        Lista de previsões realizadas
    """
    registrar_requisicao("consultas")
    previsoes = db.query(Previsao).order_by(desc(Previsao.timestamp)).offset(offset).limit(limit).all()
    return [previsao.to_dict() for previsao in previsoes]

@router.get("/treinamentos", response_model=List[ModeloDetail], tags=["historico"])
async def listar_treinamentos(
    limit: int = Query(10, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lista o histórico de treinamentos realizados.
    
    Args:
        limit: Limite de resultados
        offset: Offset para paginação
        db: Sessão do banco de dados
        
    Returns:
        Lista de treinamentos realizados
    """
    registrar_requisicao("consultas")
    treinamentos = db.query(ModeloTreinamento).order_by(desc(ModeloTreinamento.timestamp)).offset(offset).limit(limit).all()
    return [treinamento.to_dict() for treinamento in treinamentos]

@router.get("/treinamentos/{treinamento_id}", response_model=Dict[str, Any], tags=["historico"])
async def obter_treinamento(
    treinamento_id: int = Path(..., description="ID do treinamento"), 
    include_samples: bool = Query(False, description="Incluir os dados de treinamento?"),
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de um treinamento específico.
    
    Args:
        treinamento_id: ID do treinamento
        include_samples: Indica se deve incluir amostras de treinamento
        db: Sessão do banco de dados
        
    Returns:
        Detalhes do treinamento
    """
    registrar_requisicao("consultas")
    treinamento = db.query(ModeloTreinamento).filter(ModeloTreinamento.id == treinamento_id).first()
    
    if not treinamento:
        raise HTTPException(status_code=404, detail="Treinamento não encontrado")
    
    result = treinamento.to_dict()
    
    if include_samples:
        amostras = db.query(DadoTreinamento).filter(DadoTreinamento.modelo_id == treinamento_id).all()
        result["amostras"] = [amostra.to_dict() for amostra in amostras]
    
    return result

@router.get("/status", response_model=StatusOutput, tags=["info"])
async def status(request: Request, db: Session = Depends(get_db)):
    """
    Obtém o status atual da API e do modelo.
    
    Args:
        request: Objeto da requisição
        db: Sessão do banco de dados
        
    Returns:
        Status atual da API e modelo
    """
    registrar_requisicao("consultas")
    
    # Verificar se o modelo está carregado
    modelo_carregado = ml_service.modelo_treinado
    
    # Verificar se há arquivo de modelo salvo
    modelo_salvo = False
    try:
        modelo_salvo = os.path.exists(os.path.join(ml_service.modelo_dir, 'modelo_pipeline.pkl'))
    except:
        pass
    
    # Obter estatísticas do banco de dados
    estatisticas_db = {
        "total_treinamentos": db.query(func.count(ModeloTreinamento.id)).scalar(),
        "total_previsoes": db.query(func.count(Previsao.id)).scalar(),
        "ultimo_treinamento": None
    }
    
    # Obter último treinamento
    ultimo_modelo = db.query(ModeloTreinamento).order_by(desc(ModeloTreinamento.timestamp)).first()
    if ultimo_modelo:
        estatisticas_db["ultimo_treinamento"] = ultimo_modelo.timestamp.isoformat()
        estatisticas_db["r2_score_ultimo_modelo"] = ultimo_modelo.r2_score
    
    resposta = {
        "modelo_salvo": modelo_salvo,
        "modelo_carregado": modelo_carregado,
        "features_suportadas": ml_service.feature_names,
        "algoritmo_atual": getattr(ml_service.pipeline, "algoritmo", None) if modelo_carregado else None,
        "metricas_modelo": ml_service.metricas if modelo_carregado else None,
        "numero_amostras_treinamento": ultimo_modelo.num_amostras if ultimo_modelo else None,
        "estatisticas_api": get_estatisticas(),
        "metricas_banco_dados": estatisticas_db
    }
    
    return resposta 