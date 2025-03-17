import os
import uuid
import json
import httpx
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import pandas as pd
import numpy as np

from ..config import Config

# Funções para manipulação de dados
def gerar_id_unico() -> str:
    """
    Gera um ID único para requisições ou tarefas.
    
    Returns:
        str: ID único no formato UUID4
    """
    return str(uuid.uuid4())

def converter_para_json_serializavel(obj: Any) -> Any:
    """
    Converte objetos para formatos serializáveis em JSON.
    
    Args:
        obj: Objeto a ser convertido
        
    Returns:
        Objeto convertido para formato serializável
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
        return float(obj) if np.issubdtype(type(obj), np.floating) else int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {k: converter_para_json_serializavel(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [converter_para_json_serializavel(i) for i in obj]
    return obj

def salvar_json(dados: Any, caminho: str) -> bool:
    """
    Salva dados em formato JSON.
    
    Args:
        dados: Dados a serem salvos
        caminho: Caminho do arquivo
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        # Converter para formato serializável
        dados_serializaveis = converter_para_json_serializavel(dados)
        
        # Salvar no arquivo
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados_serializaveis, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar JSON: {str(e)}")
        return False

def carregar_json(caminho: str) -> Optional[Dict]:
    """
    Carrega dados de um arquivo JSON.
    
    Args:
        caminho: Caminho do arquivo
        
    Returns:
        Dict: Dados carregados ou None se ocorrer erro
    """
    try:
        if not os.path.exists(caminho):
            return None
        
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON: {str(e)}")
        return None

# Funções para manipulação de DataFrames
def validar_dataframe(df: pd.DataFrame, colunas_obrigatorias: List[str]) -> bool:
    """
    Valida se um DataFrame contém as colunas obrigatórias.
    
    Args:
        df: DataFrame a ser validado
        colunas_obrigatorias: Lista de colunas que devem estar presentes
        
    Returns:
        bool: True se o DataFrame é válido, False caso contrário
    """
    if df is None or df.empty:
        return False
    
    return all(coluna in df.columns for coluna in colunas_obrigatorias)

def converter_lista_para_dataframe(dados: List[Dict]) -> pd.DataFrame:
    """
    Converte uma lista de dicionários para DataFrame.
    
    Args:
        dados: Lista de dicionários com dados
        
    Returns:
        DataFrame: DataFrame criado a partir dos dados
    """
    return pd.DataFrame(dados)

# Funções para comunicação com serviços externos
async def verificar_status_celery(url: str = None) -> Dict[str, Any]:
    """
    Verifica o status do Celery através da API Flower.
    
    Args:
        url: URL da API Flower. Se None, usa a configurada.
        
    Returns:
        Dict: Informações sobre o status do Celery
    """
    if url is None:
        url = Config.FLOWER_URL
    
    try:
        async with httpx.AsyncClient() as client:
            # Obter informações dos workers
            workers_response = await client.get(f"{url}/api/workers")
            workers_data = workers_response.json()
            
            # Obter informações das tarefas
            tasks_response = await client.get(f"{url}/api/tasks")
            tasks_data = tasks_response.json()
            
            # Processar informações dos workers
            workers_info = []
            for worker_name, worker_data in workers_data.items():
                workers_info.append({
                    "id": worker_name,
                    "status": "online" if worker_data.get("status") else "offline",
                    "tarefas_processadas": worker_data.get("stats", {}).get("total", 0),
                    "tarefas_ativas": len(worker_data.get("active_tasks", {}))
                })
            
            # Contar tarefas por fila
            filas = {}
            for task_id, task_data in tasks_data.items():
                queue = task_data.get("queue", "celery")
                filas[queue] = filas.get(queue, 0) + 1
            
            # Montar resposta
            return {
                "status": "online" if workers_info else "offline",
                "workers": workers_info,
                "filas": filas,
                "total_workers": len(workers_info),
                "total_tarefas_ativas": sum(w["tarefas_ativas"] for w in workers_info)
            }
    except Exception as e:
        # Em caso de erro, retornar status offline
        return {
            "status": "offline",
            "erro": str(e),
            "workers": [],
            "filas": {},
            "total_workers": 0,
            "total_tarefas_ativas": 0
        } 