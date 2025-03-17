#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from celery import Celery, signals
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import sqlalchemy
from sqlalchemy.orm import Session

from .config import Config
from .utils.logger import app_logger
from .ml.models import ModeloPrecoImovel
from .database.database import SessionLocal
from .database.models import Tarefa
from .utils.metrics import CELERY_QUEUE_SIZE, ERROR_COUNTER

# Configuração do Celery
app = Celery(
    'app10',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)

# Configurações adicionais do Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora (em segundos)
    worker_prefetch_multiplier=1,  # Evitar que o worker pegue muitas tarefas de uma vez
    task_acks_late=True,   # Confirmar tarefa apenas após execução
    task_reject_on_worker_lost=True,  # Rejeitar tarefa se o worker morrer
    task_default_queue='default',  # Fila padrão
    broker_connection_retry=True,  # Reconectar automaticamente ao broker
    broker_connection_retry_on_startup=True,  # Reconectar automaticamente ao iniciar
    broker_connection_max_retries=10,  # Número máximo de tentativas de reconexão
    result_expires=86400,  # Resultados expiram após 24 horas
)

# Instância do modelo de ML
modelo = ModeloPrecoImovel()

# Carregar modelo ao iniciar worker
@signals.worker_ready.connect
def on_worker_ready(**kwargs):
    """
    Executado quando o worker está pronto para receber tarefas.
    """
    app_logger.info("Worker inicializado e pronto para processar tarefas")
    try:
        modelo.carregar_modelo()
        app_logger.info("Modelo carregado com sucesso no worker")
    except Exception as e:
        app_logger.warning(f"Não foi possível carregar o modelo: {str(e)}")

# Monitorar tamanho das filas
@signals.heartbeat_sent.connect
def monitor_queue_size(sender, **kwargs):
    """
    Monitorar o tamanho das filas a cada batimento do Celery.
    """
    try:
        inspector = app.control.inspect()
        queues = inspector.active_queues() or {}
        
        for worker_name, worker_queues in queues.items():
            for queue in worker_queues:
                queue_name = queue.get('name', 'unknown')
                # O tamanho real exigiria interação com Redis/RabbitMQ
                # Aqui estamos apenas registrando as filas ativas
                CELERY_QUEUE_SIZE.labels(queue_name=queue_name).set(0)
        
    except Exception as e:
        app_logger.error(f"Erro ao monitorar filas: {str(e)}")

# Função para atualizar status da tarefa no banco de dados
def atualizar_status_tarefa(task_id: str, status: str, resultado: Optional[Dict] = None, 
                          erro: Optional[str] = None) -> bool:
    """
    Atualiza o status de uma tarefa no banco de dados.
    
    Args:
        task_id: ID da tarefa
        status: Status atual ('pendente', 'em_progresso', 'concluida', 'falha')
        resultado: Resultado da tarefa, se concluída
        erro: Mensagem de erro, se falhou
    
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    try:
        db = SessionLocal()
        try:
            # Buscar tarefa
            tarefa = db.query(Tarefa).filter(Tarefa.task_id == task_id).first()
            
            if not tarefa:
                app_logger.warning(f"Tarefa não encontrada: {task_id}")
                return False
            
            # Atualizar status
            tarefa.status = status
            
            if resultado:
                tarefa.resultado = resultado
            
            if erro:
                tarefa.erro = erro
            
            # Calcular duração se a tarefa foi concluída
            if status in ['concluida', 'falha'] and tarefa.timestamp_inicio:
                inicio = tarefa.timestamp_inicio
                if isinstance(inicio, str):
                    inicio = datetime.fromisoformat(inicio)
                duracao = (datetime.utcnow() - inicio).total_seconds()
                tarefa.duracao = duracao
            
            # Atualizar timestamp
            tarefa.timestamp_atualizacao = datetime.utcnow()
            
            # Commit das alterações
            db.commit()
            return True
        
        except Exception as e:
            db.rollback()
            app_logger.error(f"Erro ao atualizar status da tarefa {task_id}: {str(e)}")
            ERROR_COUNTER.labels(type="database", location="atualizar_status_tarefa").inc()
            return False
        
        finally:
            db.close()
    
    except Exception as e:
        app_logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        ERROR_COUNTER.labels(type="database_connection", location="atualizar_status_tarefa").inc()
        return False

# Tarefa Celery para treinamento de modelo
@app.task(bind=True, name='treinar_modelo')
def treinar_modelo(self, dados: List[Dict[str, Any]], algoritmo: str = None) -> Dict[str, Any]:
    """
    Tarefa para treinar o modelo de ML de forma assíncrona.
    
    Args:
        dados: Lista de dicionários com os dados de treinamento
        algoritmo: Nome do algoritmo a ser utilizado
    
    Returns:
        Dict[str, Any]: Métricas e informações do modelo treinado
    """
    task_id = self.request.id
    app_logger.info(f"Iniciando tarefa de treinamento: {task_id}")
    
    # Atualizar status para 'em_progresso'
    atualizar_status_tarefa(task_id, 'em_progresso')
    
    try:
        # Treinar o modelo
        inicio = time.time()
        metricas = modelo.treinar(dados, algoritmo)
        duracao = time.time() - inicio
        
        # Preparar resultado
        resultado = {
            **metricas,
            'algoritmo': algoritmo or modelo.algoritmo,
            'tempo_treinamento': duracao,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Atualizar status para 'concluida'
        atualizar_status_tarefa(task_id, 'concluida', resultado=resultado)
        
        app_logger.info(f"Tarefa de treinamento concluída: {task_id}")
        return resultado
    
    except Exception as e:
        erro = str(e)
        app_logger.error(f"Erro na tarefa de treinamento {task_id}: {erro}", exc_info=True)
        
        # Atualizar status para 'falha'
        atualizar_status_tarefa(task_id, 'falha', erro=erro)
        
        # Registrar erro
        ERROR_COUNTER.labels(type="task_error", location="treinar_modelo").inc()
        
        # Recriar exceção para o Celery
        raise

# Tarefa Celery para previsão
@app.task(bind=True, name='realizar_previsao')
def realizar_previsao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarefa para realizar previsões de forma assíncrona.
    
    Args:
        dados: Dicionário com os dados para previsão
    
    Returns:
        Dict[str, Any]: Resultado da previsão
    """
    task_id = self.request.id
    app_logger.info(f"Iniciando tarefa de previsão: {task_id}")
    
    # Atualizar status para 'em_progresso'
    atualizar_status_tarefa(task_id, 'em_progresso')
    
    try:
        # Realizar previsão
        inicio = time.time()
        preco_previsto, confianca = modelo.prever(dados)
        duracao = time.time() - inicio
        
        # Preparar resultado
        resultado = {
            'preco_previsto': preco_previsto,
            'confianca': confianca,
            'modelo_usado': modelo.algoritmo,
            'tempo_predicao': duracao,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Atualizar status para 'concluida'
        atualizar_status_tarefa(task_id, 'concluida', resultado=resultado)
        
        app_logger.info(f"Tarefa de previsão concluída: {task_id}")
        return resultado
    
    except Exception as e:
        erro = str(e)
        app_logger.error(f"Erro na tarefa de previsão {task_id}: {erro}", exc_info=True)
        
        # Atualizar status para 'falha'
        atualizar_status_tarefa(task_id, 'falha', erro=erro)
        
        # Registrar erro
        ERROR_COUNTER.labels(type="task_error", location="realizar_previsao").inc()
        
        # Recriar exceção para o Celery
        raise

# Tarefa periódica para limpeza de tarefas antigas
@app.task(name='limpar_tarefas_antigas')
def limpar_tarefas_antigas(dias: int = 30) -> Dict[str, Any]:
    """
    Tarefa para limpar tarefas antigas do banco de dados.
    
    Args:
        dias: Número de dias para manter tarefas
    
    Returns:
        Dict[str, Any]: Resultado da limpeza
    """
    app_logger.info(f"Iniciando limpeza de tarefas antigas (mais de {dias} dias)")
    
    try:
        db = SessionLocal()
        try:
            # Calcular data limite
            data_limite = datetime.utcnow() - datetime.timedelta(days=dias)
            
            # Remover tarefas antigas
            resultado = db.query(Tarefa).filter(Tarefa.timestamp_atualizacao < data_limite).delete()
            
            # Commit das alterações
            db.commit()
            
            app_logger.info(f"Limpeza concluída: {resultado} tarefas removidas")
            return {'tarefas_removidas': resultado}
        
        except Exception as e:
            db.rollback()
            erro = str(e)
            app_logger.error(f"Erro ao limpar tarefas antigas: {erro}", exc_info=True)
            
            # Registrar erro
            ERROR_COUNTER.labels(type="task_error", location="limpar_tarefas_antigas").inc()
            
            # Recriar exceção para o Celery
            raise
        
        finally:
            db.close()
    
    except Exception as e:
        app_logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        ERROR_COUNTER.labels(type="database_connection", location="limpar_tarefas_antigas").inc()
        raise

# Configuração de tarefas periódicas
app.conf.beat_schedule = {
    'limpar-tarefas-antigas': {
        'task': 'limpar_tarefas_antigas',
        'schedule': 86400.0,  # 24 horas
        'args': (30,),  # manter tarefas por 30 dias
    },
}

# Iniciar worker se o script for executado diretamente
if __name__ == "__main__":
    app.start() 