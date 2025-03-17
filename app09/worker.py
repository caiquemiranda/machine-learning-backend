#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from celery import Celery
from celery.signals import task_success, task_failure, task_revoked
import pandas as pd
import numpy as np
import joblib
from sqlalchemy.orm import Session

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'worker.log'))
    ]
)
logger = logging.getLogger('celery_worker')

# Importações locais
try:
    from config import Config
    from database.database import get_db
    from database.models import StatusTarefa
    from ml.models import ModeloPrecoImovel
except ImportError:
    # Quando executado diretamente, ajusta o path
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app9.config import Config
    from app9.database.database import get_db
    from app9.database.models import StatusTarefa
    from app9.ml.models import ModeloPrecoImovel

# Configuração do Celery
app = Celery('app9')
app.conf.broker_url = Config.CELERY_BROKER_URL
app.conf.result_backend = Config.CELERY_RESULT_BACKEND

# Configurações adicionais do Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,  # Controle de concorrência
)

# Instância do modelo de ML
modelo = ModeloPrecoImovel()

# Funções auxiliares para atualizar o status das tarefas no banco de dados
def atualizar_status_tarefa(task_id, status, resultado=None, erro=None):
    """Atualiza o status de uma tarefa no banco de dados"""
    try:
        db = next(get_db())
        tarefa = db.query(StatusTarefa).filter(StatusTarefa.task_id == task_id).first()
        
        if tarefa:
            tarefa.status = status
            if resultado is not None:
                tarefa.resultado = str(resultado)
            if erro is not None:
                tarefa.erro = str(erro)
            
            db.commit()
            logger.info(f"Status da tarefa {task_id} atualizado para {status}")
        else:
            logger.warning(f"Tarefa {task_id} não encontrada no banco de dados")
    except Exception as e:
        logger.error(f"Erro ao atualizar status da tarefa {task_id}: {str(e)}")
    finally:
        db.close()

# Handlers para eventos de tarefas
@task_success.connect
def tarefa_bem_sucedida(sender=None, result=None, **kwargs):
    """Handler para quando uma tarefa é concluída com sucesso"""
    task_id = sender.request.id
    logger.info(f"Tarefa {task_id} concluída com sucesso")
    atualizar_status_tarefa(task_id, "CONCLUIDO", resultado=result)

@task_failure.connect
def tarefa_falhou(sender=None, exception=None, **kwargs):
    """Handler para quando uma tarefa falha"""
    task_id = sender.request.id
    logger.error(f"Tarefa {task_id} falhou: {str(exception)}")
    atualizar_status_tarefa(task_id, "FALHA", erro=str(exception))

@task_revoked.connect
def tarefa_cancelada(sender=None, **kwargs):
    """Handler para quando uma tarefa é cancelada"""
    task_id = sender.request.id
    logger.warning(f"Tarefa {task_id} foi cancelada")
    atualizar_status_tarefa(task_id, "CANCELADO")

# Tarefas assíncronas
@app.task(bind=True, name="treinar_modelo")
def treinar_modelo(self, dados_treino, algoritmo=Config.DEFAULT_ALGORITHM):
    """
    Tarefa assíncrona para treinar o modelo de ML
    
    Args:
        dados_treino (dict): Dicionário com os dados de treino
        algoritmo (str): Algoritmo a ser utilizado
        
    Returns:
        dict: Métricas do modelo treinado
    """
    task_id = self.request.id
    logger.info(f"Iniciando treinamento assíncrono (ID: {task_id}) com algoritmo {algoritmo}")
    
    try:
        # Atualiza status para EM_PROGRESSO
        atualizar_status_tarefa(task_id, "EM_PROGRESSO")
        
        # Converte dados para DataFrame
        df = pd.DataFrame(dados_treino)
        
        # Treina o modelo
        metricas = modelo.treinar(df, algoritmo)
        
        # Salva o modelo treinado
        modelo.salvar_modelo()
        
        logger.info(f"Treinamento concluído (ID: {task_id}). Métricas: {metricas}")
        return metricas
        
    except Exception as e:
        logger.error(f"Erro no treinamento (ID: {task_id}): {str(e)}")
        raise

@app.task(bind=True, name="fazer_previsao")
def fazer_previsao(self, dados_entrada):
    """
    Tarefa assíncrona para fazer previsões com o modelo
    
    Args:
        dados_entrada (dict): Dicionário com os dados de entrada
        
    Returns:
        dict: Resultado da previsão
    """
    task_id = self.request.id
    logger.info(f"Iniciando previsão assíncrona (ID: {task_id})")
    
    try:
        # Atualiza status para EM_PROGRESSO
        atualizar_status_tarefa(task_id, "EM_PROGRESSO")
        
        # Verifica se é uma única previsão ou em lote
        if isinstance(dados_entrada, dict):
            # Previsão única
            resultado = modelo.prever(dados_entrada)
            logger.info(f"Previsão única concluída (ID: {task_id})")
            return {"previsao": resultado}
        else:
            # Previsão em lote
            df = pd.DataFrame(dados_entrada)
            resultados = modelo.prever_lote(df)
            logger.info(f"Previsão em lote concluída (ID: {task_id}). Total: {len(resultados)}")
            return {"previsoes": resultados}
            
    except Exception as e:
        logger.error(f"Erro na previsão (ID: {task_id}): {str(e)}")
        raise

@app.task(bind=True, name="verificar_status")
def verificar_status(self):
    """
    Tarefa para verificar o status do worker e do modelo
    
    Returns:
        dict: Informações sobre o status do worker e do modelo
    """
    task_id = self.request.id
    logger.info(f"Verificando status (ID: {task_id})")
    
    try:
        # Verifica se o modelo está carregado
        modelo_carregado = modelo.modelo is not None
        
        # Obtém informações do modelo se estiver carregado
        if modelo_carregado:
            info_modelo = {
                "algoritmo": modelo.algoritmo,
                "features": modelo.features,
                "treinado_em": modelo.data_treinamento.isoformat() if modelo.data_treinamento else None
            }
        else:
            info_modelo = None
        
        # Retorna informações de status
        return {
            "worker_id": self.request.hostname,
            "modelo_carregado": modelo_carregado,
            "info_modelo": info_modelo,
            "celery_status": "online"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status (ID: {task_id}): {str(e)}")
        raise

if __name__ == "__main__":
    # Quando executado diretamente, inicia o worker
    app.start() 