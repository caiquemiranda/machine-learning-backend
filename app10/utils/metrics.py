#!/usr/bin/env python
# -*- coding: utf-8 -*-

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps

# Métricas de requisições HTTP
HTTP_REQUEST_COUNTER = Counter(
    'http_requests_total', 
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duração das requisições HTTP em segundos',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
)

# Métricas de predições
PREDICTIONS_COUNTER = Counter(
    'ml_predictions_total',
    'Total de predições realizadas',
    ['model_type', 'success']
)

PREDICTION_DURATION = Histogram(
    'ml_prediction_duration_seconds',
    'Duração das predições em segundos',
    ['model_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, float('inf'))
)

# Métricas de treinamento
TRAINING_COUNTER = Counter(
    'ml_training_total',
    'Total de treinamentos realizados',
    ['model_type', 'success']
)

TRAINING_DURATION = Histogram(
    'ml_training_duration_seconds',
    'Duração dos treinamentos em segundos',
    ['model_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, float('inf'))
)

# Métricas do sistema
MODEL_LOADED = Gauge(
    'ml_model_loaded',
    'Indica se o modelo está carregado (1) ou não (0)',
    ['model_type']
)

CELERY_QUEUE_SIZE = Gauge(
    'celery_queue_size',
    'Número de tarefas na fila do Celery',
    ['queue_name']
)

# Métricas de erro
ERROR_COUNTER = Counter(
    'app_errors_total',
    'Total de erros ocorridos',
    ['type', 'location']
)

# Decorator para medir tempo de execução de funções
def measure_time(metric, labels=None):
    """
    Decorator para medir o tempo de execução de uma função.
    
    Args:
        metric: Métrica Prometheus (Histogram ou Summary)
        labels: Dicionário com labels para a métrica
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator

# Middleware para medir tempo de requisições HTTP
def track_requests(response, request, duration):
    """
    Função para registrar métricas de requisições HTTP.
    
    Args:
        response: Resposta HTTP
        request: Requisição HTTP
        duration: Duração da requisição em segundos
    """
    status = response.status_code
    method = request.method
    endpoint = request.url.path
    
    HTTP_REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status=status).inc()
    HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration) 