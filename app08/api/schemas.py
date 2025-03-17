#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, List, Optional, Any, Tuple, Union

class PrevisaoInput(BaseModel):
    """
    Esquema para entrada de previsão
    """
    area: float = Field(..., description="Área do imóvel em metros quadrados", gt=0)
    quartos: Optional[int] = Field(None, description="Número de quartos", ge=0)
    banheiros: Optional[int] = Field(None, description="Número de banheiros", ge=0)
    idade_imovel: Optional[int] = Field(None, description="Idade do imóvel em anos", ge=0)
    
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