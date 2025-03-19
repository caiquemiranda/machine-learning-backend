from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import pandas as pd
import os
import logging
from datetime import datetime

from database import get_db, init_db, TipoSolicitacao, Estimativa
from model import EstimadorTempoAtendimento

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="API de Estimativa de Tempo de Atendimento",
    description="API para estimar tempo de atendimento baseado em tipo de solicitação e complexidade",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar modelo
estimador = EstimadorTempoAtendimento(model_type="random_forest")

# Tentar carregar modelo existente
try:
    estimador.load_model()
    logger.info("Modelo carregado com sucesso.")
except FileNotFoundError:
    logger.warning("Modelo não encontrado. É necessário treinar um novo modelo.")

# Modelos Pydantic para validação de dados
from pydantic import BaseModel, Field, validator

class TipoSolicitacaoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None

class TipoSolicitacaoResponse(TipoSolicitacaoCreate):
    id: int
    
    class Config:
        orm_mode = True

class EstimativaCreate(BaseModel):
    tipo_solicitacao_id: int
    complexidade: int = Field(..., ge=1, le=5)
    tempo_real: Optional[float] = None
    observacoes: Optional[str] = None
    
    @validator('complexidade')
    def validar_complexidade(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Complexidade deve estar entre 1 e 5')
        return v

class EstimativaResponse(EstimativaCreate):
    id: int
    tempo_estimado: float
    data_criacao: datetime
    
    class Config:
        orm_mode = True

class EstimativaPredicaoRequest(BaseModel):
    tipo_solicitacao_id: int
    complexidade: int = Field(..., ge=1, le=5)

class EstimativaPredicaoResponse(BaseModel):
    tipo_solicitacao: str
    complexidade: int
    tempo_estimado: float

class ModeloMetricas(BaseModel):
    mse: float
    rmse: float
    mae: float
    r2: float

class TreinamentoResponse(BaseModel):
    status: str
    message: str
    metricas: Optional[ModeloMetricas] = None

# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    # Inicializar banco de dados
    init_db()
    logger.info("Banco de dados inicializado.")

# Endpoints da API

@app.get("/", response_class=JSONResponse)
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    return {"message": "API de Estimativa de Tempo de Atendimento", "status": "online"}

# Endpoints para tipos de solicitação
@app.post("/tipos-solicitacao/", response_model=TipoSolicitacaoResponse)
async def criar_tipo_solicitacao(tipo: TipoSolicitacaoCreate, db: Session = Depends(get_db)):
    """Criar um novo tipo de solicitação."""
    db_tipo = TipoSolicitacao(nome=tipo.nome, descricao=tipo.descricao)
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

@app.get("/tipos-solicitacao/", response_model=List[TipoSolicitacaoResponse])
async def listar_tipos_solicitacao(db: Session = Depends(get_db)):
    """Listar todos os tipos de solicitação."""
    return db.query(TipoSolicitacao).all()

@app.get("/tipos-solicitacao/{tipo_id}", response_model=TipoSolicitacaoResponse)
async def obter_tipo_solicitacao(tipo_id: int, db: Session = Depends(get_db)):
    """Obter um tipo de solicitação específico pelo ID."""
    db_tipo = db.query(TipoSolicitacao).filter(TipoSolicitacao.id == tipo_id).first()
    if db_tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de solicitação não encontrado")
    return db_tipo

# Endpoints para estimativas
@app.post("/estimativas/", response_model=EstimativaResponse)
async def criar_estimativa(estimativa: EstimativaCreate, db: Session = Depends(get_db)):
    """Criar uma nova estimativa de tempo."""
    # Verificar se o tipo de solicitação existe
    tipo_solicitacao = db.query(TipoSolicitacao).filter(TipoSolicitacao.id == estimativa.tipo_solicitacao_id).first()
    if tipo_solicitacao is None:
        raise HTTPException(status_code=404, detail="Tipo de solicitação não encontrado")
    
    # Verificar se o modelo está treinado
    if not estimador.is_trained:
        raise HTTPException(status_code=400, detail="O modelo não está treinado. Treine o modelo primeiro.")
    
    # Fazer previsão
    tempo_estimado = estimador.predict(tipo_solicitacao.nome, estimativa.complexidade)
    
    # Criar estimativa no banco de dados
    db_estimativa = Estimativa(
        tipo_solicitacao_id=estimativa.tipo_solicitacao_id,
        complexidade=estimativa.complexidade,
        tempo_estimado=tempo_estimado,
        tempo_real=estimativa.tempo_real,
        observacoes=estimativa.observacoes
    )
    
    db.add(db_estimativa)
    db.commit()
    db.refresh(db_estimativa)
    
    return db_estimativa

@app.get("/estimativas/", response_model=List[EstimativaResponse])
async def listar_estimativas(
    skip: int = 0, 
    limit: int = 100, 
    tipo_solicitacao_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Listar estimativas de tempo com paginação e filtro opcional."""
    query = db.query(Estimativa)
    
    if tipo_solicitacao_id is not None:
        query = query.filter(Estimativa.tipo_solicitacao_id == tipo_solicitacao_id)
    
    return query.offset(skip).limit(limit).all()

@app.get("/estimativas/{estimativa_id}", response_model=EstimativaResponse)
async def obter_estimativa(estimativa_id: int, db: Session = Depends(get_db)):
    """Obter uma estimativa específica pelo ID."""
    db_estimativa = db.query(Estimativa).filter(Estimativa.id == estimativa_id).first()
    if db_estimativa is None:
        raise HTTPException(status_code=404, detail="Estimativa não encontrada")
    return db_estimativa

@app.post("/predict/", response_model=EstimativaPredicaoResponse)
async def prever_tempo(request: EstimativaPredicaoRequest, db: Session = Depends(get_db)):
    """Fazer uma previsão de tempo de atendimento sem salvar no banco de dados."""
    # Verificar se o modelo está treinado
    if not estimador.is_trained:
        raise HTTPException(status_code=400, detail="O modelo não está treinado. Treine o modelo primeiro.")
    
    # Verificar se o tipo de solicitação existe
    tipo_solicitacao = db.query(TipoSolicitacao).filter(TipoSolicitacao.id == request.tipo_solicitacao_id).first()
    if tipo_solicitacao is None:
        raise HTTPException(status_code=404, detail="Tipo de solicitação não encontrado")
    
    # Fazer previsão
    tempo_estimado = estimador.predict(tipo_solicitacao.nome, request.complexidade)
    
    return {
        "tipo_solicitacao": tipo_solicitacao.nome,
        "complexidade": request.complexidade,
        "tempo_estimado": tempo_estimado
    }

@app.post("/treinar-modelo/", response_model=TreinamentoResponse)
async def treinar_modelo(db: Session = Depends(get_db)):
    """Treinar modelo com dados existentes no banco de dados."""
    # Obter todos os dados de estimativas que têm tempo real
    estimativas = db.query(Estimativa).filter(Estimativa.tempo_real.isnot(None)).all()
    
    if len(estimativas) < 10:
        return {
            "status": "error",
            "message": f"Dados insuficientes para treinamento. É necessário pelo menos 10 registros com tempo real, mas encontramos apenas {len(estimativas)}."
        }
    
    # Preparar dados para treinamento
    dados_treinamento = []
    for est in estimativas:
        tipo = db.query(TipoSolicitacao).filter(TipoSolicitacao.id == est.tipo_solicitacao_id).first()
        if tipo:
            dados_treinamento.append({
                "tipo_solicitacao": tipo.nome,
                "complexidade": est.complexidade,
                "tempo_atendimento": est.tempo_real
            })
    
    # Converter para DataFrame
    df_treinamento = pd.DataFrame(dados_treinamento)
    
    # Treinar modelo
    metricas = estimador.train(df_treinamento)
    
    # Salvar modelo
    estimador.save_model()
    
    return {
        "status": "success",
        "message": f"Modelo treinado com sucesso utilizando {len(dados_treinamento)} registros.",
        "metricas": metricas
    }

@app.post("/upload-dados-treinamento/", response_model=TreinamentoResponse)
async def upload_dados_treinamento(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Fazer upload de arquivo CSV com dados para treinamento do modelo."""
    # Verificar extensão do arquivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV são suportados")
    
    # Salvar arquivo temporariamente
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        # Carregar dados
        df = pd.read_csv(temp_file_path)
        
        # Verificar colunas necessárias
        required_columns = ['tipo_solicitacao', 'complexidade', 'tempo_atendimento']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Coluna '{col}' não encontrada no arquivo CSV")
        
        # Importar tipos de solicitação
        tipos_unicos = df['tipo_solicitacao'].unique()
        for tipo_nome in tipos_unicos:
            tipo_existente = db.query(TipoSolicitacao).filter(TipoSolicitacao.nome == tipo_nome).first()
            if not tipo_existente:
                novo_tipo = TipoSolicitacao(nome=tipo_nome)
                db.add(novo_tipo)
        
        db.commit()
        
        # Treinar modelo
        metricas = estimador.train(df)
        
        # Salvar modelo
        estimador.save_model()
        
        return {
            "status": "success",
            "message": f"Modelo treinado com sucesso utilizando {len(df)} registros do arquivo CSV.",
            "metricas": metricas
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")
    
    finally:
        # Remover arquivo temporário
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/modelo-info/", response_model=Dict[str, Any])
async def obter_info_modelo():
    """Obter informações sobre o modelo atual."""
    if not estimador.is_trained:
        return {
            "status": "não treinado",
            "message": "O modelo ainda não foi treinado."
        }
    
    return {
        "status": "treinado",
        "tipo_modelo": estimador.model_type,
        "features": estimador.features,
        "tipos_solicitacao": list(estimador.tipo_solicitacao_mapping.keys()),
        "metricas": estimador.metrics
    }

@app.get("/visualizacoes/{tipo}")
async def obter_visualizacao(tipo: str, db: Session = Depends(get_db)):
    """Obter visualização do modelo."""
    # Verificar se o tipo de visualização é válido
    tipos_validos = ["histogram", "boxplot", "complexity"]
    if tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo de visualização inválido. Tipos válidos: {tipos_validos}")
    
    # Verificar se o modelo está treinado
    if not estimador.is_trained:
        raise HTTPException(status_code=400, detail="O modelo não está treinado. Treine o modelo primeiro.")
    
    # Obter todos os dados de estimativas que têm tempo real
    estimativas = db.query(Estimativa).filter(Estimativa.tempo_real.isnot(None)).all()
    
    if len(estimativas) < 5:
        raise HTTPException(status_code=400, detail="Dados insuficientes para gerar visualizações")
    
    # Preparar dados para visualização
    dados_viz = []
    for est in estimativas:
        tipo_solic = db.query(TipoSolicitacao).filter(TipoSolicitacao.id == est.tipo_solicitacao_id).first()
        if tipo_solic:
            dados_viz.append({
                "tipo_solicitacao": tipo_solic.nome,
                "complexidade": est.complexidade,
                "tempo_atendimento": est.tempo_real
            })
    
    # Converter para DataFrame
    df_viz = pd.DataFrame(dados_viz)
    
    # Gerar visualizações
    image_paths = estimador.generate_visualization(df_viz)
    
    # Retornar a visualização solicitada
    if tipo in image_paths:
        return FileResponse(image_paths[tipo])
    else:
        raise HTTPException(status_code=404, detail="Visualização não encontrada")

# Ponto de entrada para execução direta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 