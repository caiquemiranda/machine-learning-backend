#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
import os
import uuid
import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging
import httpx

from ..database.database import get_db
from ..database.models import ModeloTreinamento, DadoTreinamento, Previsao, TarefaAssincrona, StatusTarefa, TipoTarefa, ModeloInfo
from ..worker import celery_app, treinar_modelo, fazer_previsao, verificar_status as verificar_status_worker
from ..config import settings
from . import schemas
from ml.models import ModeloPrecoImovel
from utils.helper import gerar_id_unico, converter_para_json_serializavel, verificar_status_celery

# Configuração do logger
logger = logging.getLogger(__name__)

# Criação do router
router = APIRouter()

# Instância do modelo ML
modelo_ml = ModeloPrecoImovel()

# Injetados pela aplicação principal
ml_service = None

# Contador e métricas de API
contador_requisicoes = {
    "total": 0,
    "previsoes_sincronas": 0,
    "previsoes_assincronas": 0,
    "treinamentos_sincronos": 0,
    "treinamentos_assincronos": 0,
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
    minutos = tempo_execucao / 60
    return {
        "requisicoes": contador_requisicoes,
        "tempo_execucao_segundos": tempo_execucao,
        "media_requisicoes_por_minuto": contador_requisicoes["total"] / minutos if minutos > 0 else 0
    }

def preparar_dados_previsao(dados: schemas.PrevisaoInput, request: Request):
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

def registrar_tarefa(db: Session, task_id: str, tipo: str, parametros: Dict[str, Any] = None):
    """
    Registra uma nova tarefa assíncrona no banco de dados
    
    Args:
        db: Sessão do banco de dados
        task_id: ID da tarefa
        tipo: Tipo da tarefa ('treinamento' ou 'previsao')
        parametros: Parâmetros da tarefa
        
    Returns:
        Objeto TarefaAssincrona criado
    """
    tarefa = TarefaAssincrona(
        task_id=task_id,
        tipo=tipo,
        status=StatusTarefa.PENDENTE,
        timestamp_criacao=datetime.now(),
        parametros=parametros
    )
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa

@router.get("/", tags=["info"])
def index():
    """Retorna informações básicas da API"""
    registrar_requisicao("consultas")
    return {
        "nome": "API de Previsão de Preços de Imóveis v9.0",
        "descricao": "Uma API para prever preços de imóveis com processamento assíncrono",
        "status": "online",
        "documentacao": "/docs",
        "data": datetime.now().isoformat(),
        "suporte_assincrono": True
    }

@router.post("/treinar", response_model=Union[Dict[str, Any], schemas.TarefaResponse], tags=["modelo"])
async def treinar(
    dados: schemas.TreinamentoInput, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Treina o modelo de previsão com os dados fornecidos.
    Suporta modos síncrono e assíncrono.
    
    Args:
        dados: Dados de treinamento
        request: Objeto da requisição
        db: Sessão do banco de dados
        
    Returns:
        Informações sobre o treinamento realizado ou status da tarefa assíncrona
    """
    try:
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
        
        # Verifica se o processamento é síncrono ou assíncrono
        if dados.processamento == schemas.ProcessamentoEnum.SINCRONO:
            # Processamento síncrono
            registrar_requisicao("treinamentos_sincronos")
            logger.info(f"Iniciando treinamento SÍNCRONO com {len(dados.features)} amostras")
            
            # Treinar o modelo
            resultados = ml_service.treinar(
                X, 
                y, 
                algoritmo=dados.algoritmo, 
                hiperparametros=dados.hiperparametros, 
                db=db
            )
            
            logger.info(f"Treinamento síncrono concluído com sucesso: R² = {resultados['r2_score']:.4f}")
            return resultados
        else:
            # Processamento assíncrono
            registrar_requisicao("treinamentos_assincronos")
            logger.info(f"Iniciando treinamento ASSÍNCRONO com {len(dados.features)} amostras")
            
            # Enviar tarefa para o Celery
            task = celery_app.send_task(
                'treinar_modelo',
                args=[features_array, dados.precos.copy()],
                kwargs={
                    'algoritmo': dados.algoritmo,
                    'hiperparametros': dados.hiperparametros
                }
            )
            
            # Registrar a tarefa no banco de dados
            registrar_tarefa(
                db=db, 
                task_id=task.id, 
                tipo='treinamento',
                parametros={
                    "algoritmo": dados.algoritmo,
                    "num_amostras": len(dados.features),
                    "hiperparametros": dados.hiperparametros
                }
            )
            
            logger.info(f"Treinamento assíncrono iniciado: task_id={task.id}")
            
            # Retorna o status da tarefa
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            return schemas.TarefaResponse(
                task_id=task.id,
                status="PENDENTE",
                tipo="treinamento",
                mensagem="Treinamento iniciado. Verifique o status pela URL fornecida.",
                url_status=f"{base_url}/tarefa/{task.id}"
            )
    
    except Exception as e:
        contador_requisicoes["erros"] += 1
        logger.error(f"Erro no treinamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no treinamento: {str(e)}")

@router.post("/prever", response_model=Union[schemas.PrevisaoOutput, schemas.TarefaResponse], tags=["modelo"])
async def prever(
    dados: schemas.PrevisaoInput,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Realiza previsão de preço para um imóvel.
    Suporta processamento síncrono e assíncrono.
    
    Args:
        dados: Características do imóvel
        request: Objeto da requisição
        db: Sessão do banco de dados
        
    Returns:
        Previsão de preço ou status da tarefa assíncrona
    """
    try:
        # Verifica se o processamento é síncrono ou assíncrono
        if dados.processamento == schemas.ProcessamentoEnum.SINCRONO:
            # Processamento síncrono
            registrar_requisicao("previsoes_sincronas")
            
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
            
            logger.info(f"Previsão síncrona realizada: R$ {resposta['preco_previsto']:.2f}")
            return resposta
        else:
            # Processamento assíncrono
            registrar_requisicao("previsoes_assincronas")
            logger.info(f"Iniciando previsão ASSÍNCRONA para: area={dados.area}, quartos={dados.quartos}")
            
            # Gera um ID para a requisição
            request_id = str(uuid.uuid4())
            
            # Prepara os dados para enviar ao worker
            dados_dict = {
                "request_id": request_id,
                "area": dados.area,
                "quartos": dados.quartos,
                "banheiros": dados.banheiros,
                "idade_imovel": dados.idade_imovel
            }
            
            # Envia a tarefa para o Celery
            task = celery_app.send_task('fazer_previsao', args=[dados_dict])
            
            # Registra a tarefa no banco de dados
            registrar_tarefa(
                db=db, 
                task_id=task.id, 
                tipo='previsao',
                parametros=dados_dict
            )
            
            logger.info(f"Previsão assíncrona iniciada: task_id={task.id}")
            
            # Retorna o status da tarefa
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            return schemas.TarefaResponse(
                task_id=task.id,
                status="PENDENTE",
                tipo="previsao",
                mensagem="Previsão iniciada. Verifique o status pela URL fornecida.",
                url_status=f"{base_url}/tarefa/{task.id}"
            )
            
    except HTTPException:
        contador_requisicoes["erros"] += 1
        raise
    except Exception as e:
        contador_requisicoes["erros"] += 1
        logger.error(f"Erro na previsão: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")

@router.get("/tarefa/{task_id}", response_model=schemas.StatusTarefaResponse, tags=["tarefas"])
async def status_tarefa(
    task_id: str = Path(..., description="ID da tarefa assíncrona"),
    db: Session = Depends(get_db)
):
    """
    Verifica o status de uma tarefa assíncrona.
    
    Args:
        task_id: ID da tarefa
        db: Sessão do banco de dados
        
    Returns:
        Status atual da tarefa
    """
    registrar_requisicao("consultas")
    
    # Busca a tarefa no banco de dados
    tarefa = db.query(TarefaAssincrona).filter(TarefaAssincrona.task_id == task_id).first()
    
    if not tarefa:
        # Verifica se existe no Celery mas não foi registrada no BD
        try:
            task_result = celery_app.AsyncResult(task_id)
            
            if task_result.state == 'PENDING':
                return schemas.StatusTarefaResponse(
                    task_id=task_id,
                    status="PENDENTE",
                    tipo="desconhecido",
                    timestamp_criacao=datetime.now()
                )
            elif task_result.state == 'STARTED':
                return schemas.StatusTarefaResponse(
                    task_id=task_id,
                    status="EM_PROCESSAMENTO",
                    tipo="desconhecido",
                    timestamp_criacao=datetime.now(),
                    timestamp_inicio=datetime.now()
                )
            elif task_result.state == 'SUCCESS':
                return schemas.StatusTarefaResponse(
                    task_id=task_id,
                    status="CONCLUIDA",
                    tipo="desconhecido",
                    timestamp_criacao=datetime.now(),
                    timestamp_inicio=datetime.now(),
                    timestamp_fim=datetime.now(),
                    resultado=task_result.result
                )
            else:
                return schemas.StatusTarefaResponse(
                    task_id=task_id,
                    status="FALHA",
                    tipo="desconhecido",
                    timestamp_criacao=datetime.now(),
                    erro=str(task_result.result)
                )
        except:
            raise HTTPException(status_code=404, detail=f"Tarefa com ID {task_id} não encontrada")
    
    # Retorna o status da tarefa
    return schemas.StatusTarefaResponse(
        task_id=tarefa.task_id,
        status=tarefa.status,
        tipo=tarefa.tipo,
        timestamp_criacao=tarefa.timestamp_criacao,
        timestamp_inicio=tarefa.timestamp_inicio,
        timestamp_fim=tarefa.timestamp_fim,
        resultado=tarefa.resultado,
        erro=tarefa.erro
    )

@router.get("/tarefas", response_model=schemas.ListaTarefasResponse, tags=["tarefas"])
async def listar_tarefas(
    status: Optional[StatusTarefa] = Query(None, description="Filtrar por status"),
    tipo: Optional[TipoTarefa] = Query(None, description="Filtrar por tipo"),
    limit: int = Query(10, ge=1, le=100, description="Limite de tarefas a retornar"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db)
):
    """
    Lista as tarefas assíncronas registradas.
    
    Args:
        status: Status para filtrar (opcional)
        tipo: Tipo de tarefa para filtrar (opcional)
        limit: Número máximo de resultados
        offset: Offset para paginação
        db: Sessão do banco de dados
        
    Returns:
        Lista de tarefas assíncronas
    """
    registrar_requisicao("consultas")
    
    # Prepara a consulta base
    query = db.query(TarefaAssincrona)
    
    # Aplica filtros
    if status is not None:
        query = query.filter(TarefaAssincrona.status == status)
    
    if tipo is not None:
        query = query.filter(TarefaAssincrona.tipo == tipo)
    
    # Executa a consulta com ordenação
    tarefas = query.order_by(desc(TarefaAssincrona.timestamp_criacao)).offset(offset).limit(limit).all()
    
    # Converte para o formato de resposta
    tarefas_response = []
    for tarefa in tarefas:
        tarefas_response.append(
            schemas.StatusTarefaResponse(
                task_id=tarefa.task_id,
                status=tarefa.status,
                tipo=tarefa.tipo,
                timestamp_criacao=tarefa.timestamp_criacao,
                timestamp_inicio=tarefa.timestamp_inicio,
                timestamp_fim=tarefa.timestamp_fim,
                resultado=tarefa.resultado,
                erro=tarefa.erro
            )
        )
    
    # Contar totais
    total = query.count()
    pendentes = db.query(TarefaAssincrona).filter(TarefaAssincrona.status == StatusTarefa.PENDENTE).count()
    em_progresso = db.query(TarefaAssincrona).filter(TarefaAssincrona.status == StatusTarefa.EM_PROGRESSO).count()
    concluidas = db.query(TarefaAssincrona).filter(TarefaAssincrona.status == StatusTarefa.CONCLUIDO).count()
    falhas = db.query(TarefaAssincrona).filter(TarefaAssincrona.status == StatusTarefa.FALHA).count()
    
    # Montar resposta
    return {
        "tarefas": tarefas_response,
        "total": total,
        "pendentes": pendentes,
        "em_progresso": em_progresso,
        "concluidas": concluidas,
        "falhas": falhas
    }

@router.get("/previsoes", response_model=schemas.ListaPrevisoesResponse, tags=["historico"])
async def listar_previsoes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    inclui_assincronas: bool = Query(True, description="Incluir previsões assíncronas nos resultados"),
    db: Session = Depends(get_db)
):
    """
    Lista o histórico de previsões realizadas.
    
    Args:
        limit: Limite de resultados
        offset: Offset para paginação
        inclui_assincronas: Se deve incluir previsões feitas de forma assíncrona
        db: Sessão do banco de dados
        
    Returns:
        Lista de previsões realizadas
    """
    registrar_requisicao("consultas")
    
    # Consulta base
    query = db.query(Previsao)
    
    # Filtrar por tipo de processamento se necessário
    if not inclui_assincronas:
        query = query.filter(Previsao.task_id == None)
    
    # Executar a consulta
    previsoes = query.order_by(desc(Previsao.timestamp)).offset(offset).limit(limit).all()
    
    return [previsao.to_dict() for previsao in previsoes]

@router.get("/treinamentos", response_model=schemas.ListaTreinamentosResponse, tags=["historico"])
async def listar_treinamentos(
    limit: int = Query(10, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    inclui_assincronos: bool = Query(True, description="Incluir treinamentos assíncronos nos resultados"),
    db: Session = Depends(get_db)
):
    """
    Lista o histórico de treinamentos realizados.
    
    Args:
        limit: Limite de resultados
        offset: Offset para paginação
        inclui_assincronos: Se deve incluir treinamentos feitos de forma assíncrona
        db: Sessão do banco de dados
        
    Returns:
        Lista de treinamentos realizados
    """
    registrar_requisicao("consultas")
    
    # Consulta base
    query = db.query(ModeloTreinamento)
    
    # Filtrar por tipo de processamento se necessário
    if not inclui_assincronos:
        query = query.filter(ModeloTreinamento.task_id == None)
    
    # Executar a consulta
    treinamentos = query.order_by(desc(ModeloTreinamento.timestamp)).offset(offset).limit(limit).all()
    
    return [treinamento.to_dict() for treinamento in treinamentos]

@router.get("/treinamentos/{treinamento_id}", response_model=schemas.DetalhesTreinamentoResponse, tags=["historico"])
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
    
    # Se foi um treinamento assíncrono, busca mais detalhes
    if treinamento.task_id:
        tarefa = db.query(TarefaAssincrona).filter(TarefaAssincrona.task_id == treinamento.task_id).first()
        if tarefa:
            result["tarefa"] = {
                "status": tarefa.status,
                "timestamp_criacao": tarefa.timestamp_criacao.isoformat() if tarefa.timestamp_criacao else None,
                "timestamp_inicio": tarefa.timestamp_inicio.isoformat() if tarefa.timestamp_inicio else None,
                "timestamp_fim": tarefa.timestamp_fim.isoformat() if tarefa.timestamp_fim else None,
                "duracao_segundos": (tarefa.timestamp_fim - tarefa.timestamp_inicio).total_seconds() if (tarefa.timestamp_fim and tarefa.timestamp_inicio) else None
            }
    
    return result

@router.get("/status", response_model=schemas.StatusOutput, tags=["info"])
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
        modelo_salvo = os.path.exists(settings.model_path)
    except:
        pass
    
    # Obter estatísticas do banco de dados
    estatisticas_db = {
        "total_treinamentos": db.query(func.count(ModeloTreinamento.id)).scalar(),
        "total_previsoes": db.query(func.count(Previsao.id)).scalar(),
        "tarefas_assincronas_totais": db.query(func.count(TarefaAssincrona.id)).scalar(),
        "ultimo_treinamento": None
    }
    
    # Obter último treinamento
    ultimo_modelo = db.query(ModeloTreinamento).order_by(desc(ModeloTreinamento.timestamp)).first()
    if ultimo_modelo:
        estatisticas_db["ultimo_treinamento"] = ultimo_modelo.timestamp.isoformat()
        estatisticas_db["r2_score_ultimo_modelo"] = ultimo_modelo.r2_score
        
    # Obter contagem de tarefas por status
    tarefas_ativas = {}
    for status in StatusTarefa:
        tarefas_ativas[status.value] = db.query(func.count(TarefaAssincrona.id)).filter(
            TarefaAssincrona.status == status
        ).scalar()
    
    resposta = {
        "modelo_salvo": modelo_salvo,
        "modelo_carregado": modelo_carregado,
        "features_suportadas": ml_service.feature_names,
        "algoritmo_atual": getattr(ml_service.pipeline, "algoritmo", None) if modelo_carregado else None,
        "metricas_modelo": ml_service.metricas if modelo_carregado else None,
        "numero_amostras_treinamento": ultimo_modelo.num_amostras if ultimo_modelo else None,
        "estatisticas_api": get_estatisticas(),
        "metricas_banco_dados": estatisticas_db,
        "tarefas_ativas": tarefas_ativas,
        "suporte_assincrono": True
    }
    
    return resposta

@router.get("/status", response_model=schemas.InfoModelo)
async def status_modelo():
    """
    Retorna informações detalhadas sobre o modelo atual.
    """
    return modelo_ml.obter_info()

@router.post("/treinar", response_model=schemas.TreinamentoResponse)
async def treinar(
    dados: schemas.DadosTreinamento,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Treina o modelo com os dados fornecidos.
    Pode ser executado de forma síncrona ou assíncrona.
    """
    # Verificar se há dados suficientes
    if not dados.imoveis or len(dados.imoveis) < 10:
        raise HTTPException(
            status_code=400,
            detail="Dados insuficientes para treinamento. Forneça pelo menos 10 imóveis."
        )
    
    # Gerar ID para a requisição
    request_id = gerar_id_unico()
    
    # Se for assíncrono, criar tarefa e executar em background
    if dados.assincrono:
        # Registrar tarefa no banco de dados
        tarefa = TarefaAssincrona(
            task_id="pending",  # Será atualizado quando a tarefa for criada
            tipo=TipoTarefa.TREINAMENTO,
            status=StatusTarefa.PENDENTE,
            timestamp_criacao=datetime.now(),
            descricao=f"Treinamento com algoritmo {dados.algoritmo}",
            parametros={
                "algoritmo": dados.algoritmo,
                "hiperparametros": dados.hiperparametros,
                "num_amostras": len(dados.imoveis)
            }
        )
        db.add(tarefa)
        db.commit()
        db.refresh(tarefa)
        
        # Iniciar tarefa assíncrona
        task = treinar_modelo.delay(dados.imoveis, dados.algoritmo)
        
        # Atualizar ID da tarefa
        tarefa.task_id = task.id
        db.commit()
        
        # Retornar resposta com informações da tarefa
        return JSONResponse(
            status_code=202,
            content=schemas.TarefaResponse(
                task_id=task.id,
                tipo=TipoTarefa.TREINAMENTO,
                status=StatusTarefa.PENDENTE,
                timestamp_criacao=tarefa.timestamp_criacao,
                url_status=f"/tarefa/{task.id}"
            ).dict()
        )
    
    # Se for síncrono, treinar o modelo diretamente
    try:
        # Converter dados para DataFrame
        import pandas as pd
        df = pd.DataFrame(dados.imoveis)
        
        # Treinar o modelo
        metricas = modelo_ml.treinar(df, dados.algoritmo, dados.hiperparametros)
        
        # Salvar o modelo
        modelo_ml.salvar_modelo()
        
        # Retornar resposta com métricas
        return {
            "algoritmo": dados.algoritmo,
            "metricas": metricas,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Erro ao treinar modelo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao treinar modelo: {str(e)}"
        )

@router.post("/prever", response_model=schemas.PrevisaoResponse)
async def prever(
    dados: schemas.PrevisaoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Realiza uma previsão de preço para um imóvel.
    Pode ser executado de forma síncrona ou assíncrona.
    """
    # Verificar se o modelo está treinado
    if modelo_ml.modelo is None:
        raise HTTPException(
            status_code=400,
            detail="Modelo não treinado. Treine o modelo primeiro."
        )
    
    # Gerar ID para a requisição
    request_id = gerar_id_unico()
    
    # Se for assíncrono, criar tarefa e executar em background
    if dados.assincrono:
        # Registrar tarefa no banco de dados
        tarefa = TarefaAssincrona(
            task_id="pending",  # Será atualizado quando a tarefa for criada
            tipo=TipoTarefa.PREVISAO,
            status=StatusTarefa.PENDENTE,
            timestamp_criacao=datetime.now(),
            descricao="Previsão de preço para um imóvel",
            parametros=dados.imovel.dict()
        )
        db.add(tarefa)
        db.commit()
        db.refresh(tarefa)
        
        # Iniciar tarefa assíncrona
        task = fazer_previsao.delay(dados.imovel.dict())
        
        # Atualizar ID da tarefa
        tarefa.task_id = task.id
        db.commit()
        
        # Retornar resposta com informações da tarefa
        return JSONResponse(
            status_code=202,
            content=schemas.TarefaResponse(
                task_id=task.id,
                tipo=TipoTarefa.PREVISAO,
                status=StatusTarefa.PENDENTE,
                timestamp_criacao=tarefa.timestamp_criacao,
                url_status=f"/tarefa/{task.id}"
            ).dict()
        )
    
    # Se for síncrono, fazer a previsão diretamente
    try:
        # Fazer a previsão
        resultado = modelo_ml.prever(dados.imovel.dict())
        
        # Registrar a previsão no banco de dados
        previsao = Previsao(
            request_id=request_id,
            timestamp=datetime.now(),
            dados_entrada=dados.imovel.dict(),
            valor_previsto=resultado["valor_previsto"],
            intervalo_confianca_min=resultado["intervalo_confianca"]["min"],
            intervalo_confianca_max=resultado["intervalo_confianca"]["max"],
            modelo_id=1  # Em uma implementação real, seria obtido do banco de dados
        )
        db.add(previsao)
        db.commit()
        
        # Retornar resposta com resultado
        return resultado
    except Exception as e:
        logger.error(f"Erro ao fazer previsão: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer previsão: {str(e)}"
        )

@router.post("/prever-lote", response_model=schemas.PrevisaoLoteResponse)
async def prever_lote(
    dados: schemas.PrevisaoLoteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Realiza previsões de preço para múltiplos imóveis.
    Sempre é executado de forma assíncrona.
    """
    # Verificar se o modelo está treinado
    if modelo_ml.modelo is None:
        raise HTTPException(
            status_code=400,
            detail="Modelo não treinado. Treine o modelo primeiro."
        )
    
    # Gerar ID para a requisição
    request_id = gerar_id_unico()
    
    # Registrar tarefa no banco de dados
    tarefa = TarefaAssincrona(
        task_id="pending",  # Será atualizado quando a tarefa for criada
        tipo=TipoTarefa.PREVISAO_LOTE,
        status=StatusTarefa.PENDENTE,
        timestamp_criacao=datetime.now(),
        descricao=f"Previsão de preço para {len(dados.imoveis)} imóveis",
        parametros={"num_imoveis": len(dados.imoveis)}
    )
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    
    # Iniciar tarefa assíncrona
    task = fazer_previsao.delay([imovel.dict() for imovel in dados.imoveis])
    
    # Atualizar ID da tarefa
    tarefa.task_id = task.id
    db.commit()
    
    # Retornar resposta com informações da tarefa
    return JSONResponse(
        status_code=202,
        content=schemas.TarefaResponse(
            task_id=task.id,
            tipo=TipoTarefa.PREVISAO_LOTE,
            status=StatusTarefa.PENDENTE,
            timestamp_criacao=tarefa.timestamp_criacao,
            url_status=f"/tarefa/{task.id}"
        ).dict()
    )

@router.get("/celery-status", response_model=schemas.CeleryStatusResponse)
async def status_celery():
    """
    Verifica o status do Celery e seus workers.
    """
    try:
        # Verificar status do Celery via Flower API
        status = await verificar_status_celery()
        return status
    except Exception as e:
        logger.error(f"Erro ao verificar status do Celery: {str(e)}")
        # Em caso de erro, tentar verificar via tarefa Celery
        try:
            task = verificar_status_worker.delay()
            result = task.get(timeout=5)
            
            if result:
                return {
                    "status": "online",
                    "workers": [
                        {
                            "id": result["worker_id"],
                            "status": "online",
                            "tarefas_processadas": 1,
                            "tarefas_ativas": 0
                        }
                    ],
                    "filas": {"celery": 0},
                    "total_workers": 1,
                    "total_tarefas_ativas": 0
                }
        except Exception as inner_e:
            logger.error(f"Erro ao verificar status do Celery via tarefa: {str(inner_e)}")
        
        # Se ambos falharem, retornar offline
        return {
            "status": "offline",
            "workers": [],
            "filas": {},
            "total_workers": 0,
            "total_tarefas_ativas": 0
        } 