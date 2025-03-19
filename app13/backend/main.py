from fastapi import FastAPI, Depends, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uvicorn
import json
import pandas as pd

from database import get_db, init_db, ModelMetrics, PredictionLog, TrainingData
from model import (
    load_or_train_model, predict, generate_confusion_matrix, 
    generate_feature_importance, load_model_config, save_model_config
)

# Criar a aplicação FastAPI
app = FastAPI(title="API de Diagnóstico Preditivo")

# Permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização ao iniciar a aplicação
@app.on_event("startup")
async def startup_event():
    init_db()
    # Carregar/treinar o modelo inicial
    model, X_test, y_test, metrics = load_or_train_model()
    
    # Se há métricas (modelo treinado pela primeira vez), salvar no banco
    if metrics:
        # Salvar métricas no banco de dados
        db = next(get_db())
        db_metrics = ModelMetrics(
            model_name=metrics["model_name"],
            version=metrics["version"],
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1_score"],
            parameters=json.dumps(load_model_config()["parameters"]),
            dataset_size=metrics["dataset_size"]
        )
        db.add(db_metrics)
        db.commit()

# Classes de modelo Pydantic
class PredictionRequest(BaseModel):
    idade: int = Field(..., ge=0, le=120, description="Idade em anos")
    pressao_arterial: int = Field(..., ge=70, le=250, description="Pressão arterial sistólica")
    glicose: int = Field(..., ge=50, le=500, description="Nível de glicose")
    freq_cardiaca: int = Field(..., ge=40, le=200, description="Frequência cardíaca em bpm")
    imc: float = Field(..., ge=10, le=60, description="Índice de massa corporal")
    exercicio_semanal: float = Field(..., ge=0, le=40, description="Horas de exercício por semana")
    fumante: int = Field(..., ge=0, le=1, description="Fumante (0=não, 1=sim)")

class PredictionResponse(BaseModel):
    prediction: str
    prediction_probability: float
    all_probabilities: Dict[str, float]
    model_version: int

class MetricsResponse(BaseModel):
    id: int
    model_name: str
    version: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_date: Any
    parameters: Dict[str, Any]
    dataset_size: int

class TrainModelRequest(BaseModel):
    model_type: str = Field(..., description="Tipo de modelo: 'random_forest' ou 'logistic_regression'")
    parameters: Dict[str, Any] = Field(..., description="Parâmetros do modelo")

# Endpoint para fazer predições
@app.post("/predict", response_model=PredictionResponse)
def make_prediction(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    try:
        # Converter para dicionário para processamento
        features = request.dict()
        
        # Fazer a predição
        result = predict(features)
        
        # Salvar no log de predições
        prediction_log = PredictionLog(
            input_data=json.dumps(features),
            prediction=result["prediction"],
            prediction_probability=result["prediction_probability"],
            model_version=result["model_version"]
        )
        db.add(prediction_log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer predição: {str(e)}")

# Endpoint para retreinar o modelo
@app.post("/train", response_model=MetricsResponse)
def train_model(
    request: TrainModelRequest = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Atualizar configuração do modelo
        config = load_model_config()
        config["model_type"] = request.model_type
        config["parameters"] = request.parameters
        save_model_config(config)
        
        # Treinar novo modelo
        model, X_test, y_test, metrics = load_or_train_model(force_retrain=True)
        
        # Salvar métricas no banco de dados
        db_metrics = ModelMetrics(
            model_name=metrics["model_name"],
            version=metrics["version"],
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1_score"],
            parameters=json.dumps(request.parameters),
            dataset_size=metrics["dataset_size"]
        )
        db.add(db_metrics)
        db.commit()
        db.refresh(db_metrics)
        
        # Converter parâmetros JSON de volta para dicionário
        db_metrics.parameters = json.loads(db_metrics.parameters)
        
        return db_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao treinar modelo: {str(e)}")

# Endpoint para obter métricas do modelo
@app.get("/metrics", response_model=List[MetricsResponse])
def get_metrics(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    metrics = db.query(ModelMetrics).order_by(ModelMetrics.id.desc()).limit(limit).all()
    
    # Converter parâmetros JSON para dicionário
    for m in metrics:
        if isinstance(m.parameters, str):
            m.parameters = json.loads(m.parameters)
    
    return metrics

# Endpoint para obter métricas do modelo atual
@app.get("/metrics/current", response_model=MetricsResponse)
def get_current_metrics(db: Session = Depends(get_db)):
    config = load_model_config()
    current_version = config["version"] - 1
    
    metrics = db.query(ModelMetrics).filter(ModelMetrics.version == current_version).first()
    if not metrics:
        raise HTTPException(status_code=404, detail="Métricas para o modelo atual não encontradas")
    
    # Converter parâmetros JSON para dicionário
    if isinstance(metrics.parameters, str):
        metrics.parameters = json.loads(metrics.parameters)
    
    return metrics

# Endpoint para obter matriz de confusão
@app.get("/visualizations/confusion-matrix")
def get_confusion_matrix():
    # Carregar modelo e dados de teste
    model, X_test, y_test, _ = load_or_train_model()
    
    # Fazer predições para gerar matriz
    y_pred = model.predict(X_test)
    
    # Gerar matriz de confusão como imagem base64
    classes = sorted(set(y_test))
    matrix_image = generate_confusion_matrix(y_test, y_pred, classes)
    
    return {"image": matrix_image, "classes": classes}

# Endpoint para obter importância das features
@app.get("/visualizations/feature-importance")
def get_feature_importance():
    # Carregar modelo
    model, X_test, _, _ = load_or_train_model()
    
    # Verificar se o modelo tem importância de features
    if not hasattr(model, 'feature_importances_'):
        return JSONResponse(
            status_code=400,
            content={"detail": "O modelo atual não suporta importância de features."}
        )
    
    # Gerar gráfico de importância das features
    feature_names = X_test.columns.tolist()
    importance_image = generate_feature_importance(model, feature_names)
    
    return {"image": importance_image, "features": feature_names}

# Endpoint para adicionar dados de treinamento
@app.post("/data/add")
def add_training_data(
    data: PredictionRequest,
    label: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        # Converter para dicionário para armazenamento
        features = data.dict()
        
        # Salvar no banco de dados
        training_data = TrainingData(
            features=json.dumps(features),
            label=label,
            notes=notes
        )
        db.add(training_data)
        db.commit()
        db.refresh(training_data)
        
        return {"message": "Dados adicionados com sucesso", "id": training_data.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar dados: {str(e)}")

# Endpoint para listar logs de predição
@app.get("/logs")
def get_prediction_logs(
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    logs = db.query(PredictionLog).order_by(PredictionLog.id.desc()).limit(limit).all()
    
    # Processar logs para retornar formato adequado
    result = []
    for log in logs:
        item = {
            "id": log.id,
            "prediction": log.prediction,
            "prediction_probability": log.prediction_probability,
            "model_version": log.model_version,
            "timestamp": log.timestamp,
            "input_data": json.loads(log.input_data)
        }
        result.append(item)
    
    return result

# Endpoint para obter configuração atual do modelo
@app.get("/model/config")
def get_model_config():
    return load_model_config()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 