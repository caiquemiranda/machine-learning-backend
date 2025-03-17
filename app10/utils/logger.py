#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
import sentry_sdk

from ..config import Config


# Configuração do Sentry se o DSN estiver disponível
if Config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        environment=Config.SENTRY_ENVIRONMENT,
        traces_sample_rate=0.1,
        enable_tracing=True,
    )

# Criar diretório de logs se não existir
os.makedirs(Config.LOGS_DIR, exist_ok=True)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter personalizado para logs em formato JSON.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        
        # Adicionar informações de rastreamento do Sentry se disponíveis
        try:
            from sentry_sdk import Hub
            scope = Hub.current.scope
            if scope.span:
                log_record['trace_id'] = scope.span.trace_id
                log_record['span_id'] = scope.span.span_id
        except (ImportError, AttributeError):
            pass


def get_logger(nome_app="app", nivel=None):
    """
    Configura e retorna um logger para a aplicação.
    
    Args:
        nome_app (str): Nome da aplicação para identificação nos logs.
        nivel (str, optional): Nível de logging. Defaults para o configurado no Config.LOG_LEVEL.
    
    Returns:
        logging.Logger: Logger configurado.
    """
    if nivel is None:
        nivel = getattr(logging, Config.LOG_LEVEL.upper())
    
    logger = logging.getLogger(nome_app)
    logger.setLevel(nivel)
    
    # Limpar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(nivel)
    
    # Handler para arquivo
    log_file = Path(Config.LOGS_DIR) / f"{nome_app}.log"
    file_handler = logging.FileHandler(filename=log_file, encoding='utf-8')
    file_handler.setLevel(nivel)
    
    # Formatter para JSON
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Logger global da aplicação
app_logger = get_logger("app10") 