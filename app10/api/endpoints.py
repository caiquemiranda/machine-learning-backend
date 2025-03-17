#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
import httpx
import time

from ..config import Config
from ..database.database import get_db, check_db_status
from ..database.models import Tarefa, Predicao, ModeloTreinado
from ..ml.models import ModeloPrecoImovel
from ..utils.logger import app_logger
from ..utils.metrics import MODEL_LOADED
from ..worker import app as celery_app, treinar_modelo, realizar_previsao
from .middleware import verify_api_key
from .schemas import (
    DadosEntradaPrevisao, 
    DadosEntradaTreinamento, 
    ResultadoPrevisao, 
    ResultadoTreinamento,
    StatusTarefa,
    StatusAPI
)

# Instância do modelo
modelo = ModeloPrecoImovel()

# Router da API
router = APIRouter()

# Endpoint de informações
@router.get("/", response_model=Dict[str, Any])
async def info():
    """
    Retorna informações sobre a API.
    """
    return {
        "nome": Config.API_TITLE,
        "versao": Config.API_VERSION,
        "descricao": Config.API_DESCRIPTION,
        "docs": "/docs",
        "status": "/status",
        "endpoints": {
            "info": "/",
            "status": "/status",
            "prever": "/prever",
            "treinar": "/treinar",
            "tarefas": "/tarefas",
            "tarefa": "/tarefa/{task_id}",
            "health": "/health",
            "metrics": "/metrics",
        }
    }

# Endpoint de health check
@router.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da API.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Endpoint de previsão
@router.post("/prever", response_model=Union[ResultadoPrevisao, StatusTarefa], dependencies=[Depends(verify_api_key)])
async def prever(
    dados: DadosEntradaPrevisao, 
    async_task: bool = Query(False, description="Executar predição de forma assíncrona"),
    db: Session = Depends(get_db)
):
    """
    Realiza a previsão de preço de um imóvel.
    
    Args:
        dados: Dados do imóvel para previsão
        async_task: Se True, executa a previsão de forma assíncrona
        db: Sessão do banco de dados
    
    Returns:
        ResultadoPrevisao: Resultado da previsão
        StatusTarefa: Status da tarefa, se async_task=True
    """
    app_logger.info(f"Solicitação de previsão recebida: {dados.dict()}")
    
    # Verificar se o modelo está carregado
    if modelo.modelo is None:
        try:
            modelo.carregar_modelo()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao carregar modelo: {str(e)}"
            )
    
    # Executar de forma assíncrona ou síncrona
    if async_task:
        # Criar registro de tarefa no banco de dados
        task_id = str(uuid.uuid4())
        tarefa_db = Tarefa(
            task_id=task_id,
            tipo="predicao",
            status="pendente",
            dados_entrada=dados.dict(),
            timestamp_inicio=datetime.utcnow()
        )
        db.add(tarefa_db)
        db.commit()
        
        # Iniciar tarefa assíncrona
        task = realizar_previsao.apply_async(args=[dados.dict()], task_id=task_id)
        
        # Retornar status da tarefa
        return StatusTarefa(
            task_id=task_id,
            status="pendente",
            resultado=None,
            erro=None,
            timestamp_inicio=tarefa_db.timestamp_inicio,
            timestamp_atualizacao=tarefa_db.timestamp_atualizacao
        )
    else:
        # Executar de forma síncrona
        try:
            inicio = time.time()
            preco_previsto, confianca = modelo.prever(dados.dict())
            duracao = time.time() - inicio
            
            # Registrar predição no banco de dados
            predicao_db = Predicao(
                modelo_id=1,  # Obter ID correto do modelo ativo
                dados_entrada=dados.dict(),
                resultado=preco_previsto,
                confianca=confianca,
                duracao=duracao
            )
            db.add(predicao_db)
            db.commit()
            
            return ResultadoPrevisao(
                preco_previsto=preco_previsto,
                confianca=confianca,
                modelo_usado=modelo.algoritmo,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            app_logger.error(f"Erro ao realizar previsão: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao realizar previsão: {str(e)}"
            )

# Endpoint de treinamento
@router.post("/treinar", response_model=Union[ResultadoTreinamento, StatusTarefa], dependencies=[Depends(verify_api_key)])
async def treinar(
    dados: DadosEntradaTreinamento,
    db: Session = Depends(get_db)
):
    """
    Treina o modelo com os dados fornecidos.
    
    Args:
        dados: Dados para treinamento
        db: Sessão do banco de dados
    
    Returns:
        ResultadoTreinamento: Resultado do treinamento
        StatusTarefa: Status da tarefa, se async_task=True
    """
    app_logger.info(f"Solicitação de treinamento recebida: {len(dados.dados)} registros, algoritmo: {dados.algoritmo}")
    
    # Verificar dados mínimos para treinamento
    if len(dados.dados) < 10:
        raise HTTPException(
            status_code=400,
            detail="Quantidade insuficiente de dados para treinamento. Mínimo: 10 registros."
        )
    
    # Executar de forma assíncrona ou síncrona
    if dados.async_task:
        # Criar registro de tarefa no banco de dados
        task_id = str(uuid.uuid4())
        tarefa_db = Tarefa(
            task_id=task_id,
            tipo="treinamento",
            status="pendente",
            dados_entrada={"algoritmo": dados.algoritmo, "registros": len(dados.dados)},
            timestamp_inicio=datetime.utcnow()
        )
        db.add(tarefa_db)
        db.commit()
        
        # Iniciar tarefa assíncrona
        task = treinar_modelo.apply_async(
            args=[dados.dados, dados.algoritmo], 
            task_id=task_id
        )
        
        # Retornar status da tarefa
        return StatusTarefa(
            task_id=task_id,
            status="pendente",
            resultado=None,
            erro=None,
            timestamp_inicio=tarefa_db.timestamp_inicio,
            timestamp_atualizacao=tarefa_db.timestamp_atualizacao
        )
    else:
        # Executar de forma síncrona
        try:
            inicio = time.time()
            metricas = modelo.treinar(dados.dados, dados.algoritmo)
            duracao = time.time() - inicio
            
            # Registrar modelo treinado no banco de dados
            modelo_db = ModeloTreinado(
                nome="modelo_preco_imovel",
                algoritmo=dados.algoritmo,
                versao=Config.API_VERSION,
                arquivo=modelo.model_path,
                metricas=metricas,
                hiperparametros={},  # Adicionar parâmetros reais
                data_treinamento=datetime.utcnow(),
                ativo=True
            )
            db.add(modelo_db)
            db.commit()
            
            return ResultadoTreinamento(
                algoritmo=dados.algoritmo,
                mae=metricas.get('mae', 0),
                mse=metricas.get('mse', 0),
                r2=metricas.get('r2', 0),
                tempo_treinamento=metricas.get('tempo_treinamento', duracao),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            app_logger.error(f"Erro ao treinar modelo: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao treinar modelo: {str(e)}"
            )

# Endpoint para verificar status de uma tarefa
@router.get("/tarefa/{task_id}", response_model=StatusTarefa, dependencies=[Depends(verify_api_key)])
async def verificar_status_tarefa(
    task_id: str = Path(..., description="ID da tarefa"),
    db: Session = Depends(get_db)
):
    """
    Verifica o status de uma tarefa assíncrona.
    
    Args:
        task_id: ID da tarefa
        db: Sessão do banco de dados
    
    Returns:
        StatusTarefa: Status atual da tarefa
    """
    # Buscar tarefa no banco de dados
    tarefa = db.query(Tarefa).filter(Tarefa.task_id == task_id).first()
    
    if not tarefa:
        raise HTTPException(
            status_code=404,
            detail=f"Tarefa não encontrada: {task_id}"
        )
    
    return StatusTarefa(
        task_id=tarefa.task_id,
        status=tarefa.status,
        resultado=tarefa.resultado,
        erro=tarefa.erro,
        timestamp_inicio=tarefa.timestamp_inicio,
        timestamp_atualizacao=tarefa.timestamp_atualizacao
    )

# Endpoint para listar tarefas
@router.get("/tarefas", response_model=List[StatusTarefa], dependencies=[Depends(verify_api_key)])
async def listar_tarefas(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de tarefa (treinamento, predicao)"),
    status: Optional[str] = Query(None, description="Filtrar por status (pendente, em_progresso, concluida, falha)"),
    limite: int = Query(10, description="Limite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Lista as tarefas assíncronas.
    
    Args:
        tipo: Filtrar por tipo de tarefa
        status: Filtrar por status
        limite: Limite de resultados
        db: Sessão do banco de dados
    
    Returns:
        List[StatusTarefa]: Lista de tarefas
    """
    # Construir query
    query = db.query(Tarefa)
    
    if tipo:
        query = query.filter(Tarefa.tipo == tipo)
    
    if status:
        query = query.filter(Tarefa.status == status)
    
    # Ordenar por timestamp de atualização mais recente
    tarefas = query.order_by(Tarefa.timestamp_atualizacao.desc()).limit(limite).all()
    
    return [
        StatusTarefa(
            task_id=tarefa.task_id,
            status=tarefa.status,
            resultado=tarefa.resultado,
            erro=tarefa.erro,
            timestamp_inicio=tarefa.timestamp_inicio,
            timestamp_atualizacao=tarefa.timestamp_atualizacao
        )
        for tarefa in tarefas
    ]

# Endpoint para verificar status do Celery
@router.get("/celery-status", dependencies=[Depends(verify_api_key)])
async def verificar_status_celery():
    """
    Verifica o status do Celery e seus workers.
    
    Returns:
        Dict: Status do Celery
    """
    try:
        # Verificar status dos workers
        inspector = celery_app.control.inspect()
        
        # Obter informações dos workers ativos
        workers_ativos = inspector.active() or {}
        workers_programados = inspector.scheduled() or {}
        workers_reservados = inspector.reserved() or {}
        stats = inspector.stats() or {}
        
        return {
            "status": "online" if workers_ativos else "offline",
            "workers_ativos": len(workers_ativos),
            "tarefas_ativas": sum(len(tasks) for tasks in workers_ativos.values()),
            "tarefas_programadas": sum(len(tasks) for tasks in workers_programados.values()),
            "tarefas_reservadas": sum(len(tasks) for tasks in workers_reservados.values()),
            "detalhes": {
                "workers": list(stats.keys()),
                "stats": stats
            }
        }
    except Exception as e:
        app_logger.error(f"Erro ao verificar status do Celery: {str(e)}", exc_info=True)
        return {
            "status": "erro",
            "mensagem": str(e)
        }

# Endpoint para verificar status da API
@router.get("/status", response_model=StatusAPI)
async def verificar_status():
    """
    Verifica o status da API e seus componentes.
    
    Returns:
        StatusAPI: Status da API
    """
    # Verificar status do modelo
    status_modelo = modelo.get_status()
    
    # Verificar status do banco de dados
    status_db = check_db_status()
    
    # Verificar status do Celery
    try:
        status_celery = {
            "status": "online",
            "mensagem": "Conectado ao broker"
        }
        
        # Tentar verificar status mais detalhado
        inspector = celery_app.control.inspect()
        workers_ativos = inspector.active() or {}
        status_celery["workers"] = list(workers_ativos.keys())
    except Exception as e:
        status_celery = {
            "status": "erro",
            "mensagem": str(e)
        }
    
    return StatusAPI(
        versao=Config.API_VERSION,
        status="online",
        modelo_carregado=status_modelo["modelo_carregado"],
        ultima_atualizacao_modelo=datetime.fromtimestamp(status_modelo["ultima_atualizacao"]) if status_modelo["ultima_atualizacao"] else None,
        algoritmo_atual=status_modelo["algoritmo"],
        metricas=status_modelo["metricas"],
        status_celery=status_celery,
        status_banco_dados=status_db
    ) 