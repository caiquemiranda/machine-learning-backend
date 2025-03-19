from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import logging
from io import StringIO
from pydantic import BaseModel, Field, EmailStr

# Importações locais
from database import get_db, User, Prediction, Log, init_db
from auth import (
    Token, UserCreate, UserResponse, authenticate_user, 
    create_access_token, get_current_user, get_current_active_user,
    get_current_admin_user, get_password_hash, log_action
)
from model import get_model, MLModel

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar o aplicativo FastAPI
app = FastAPI(
    title="API de Previsões com ML",
    description="Sistema multi-usuário de previsões com autenticação JWT",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, isso deve ser substituído pelos domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Classes Pydantic para validação de dados
class PredictionRequest(BaseModel):
    prediction_type: str = Field(..., description="Tipo de previsão ('classifier' ou 'regressor')")
    input_data: Dict[str, Any] = Field(..., description="Dados de entrada para a previsão")

class PredictionResponse(BaseModel):
    id: int
    user_id: int
    prediction_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True

class TrainRequest(BaseModel):
    model_type: str = Field(..., description="Tipo de modelo ('classifier' ou 'regressor')")
    model_name: str = Field(..., description="Nome do modelo")
    training_data: Dict[str, List] = Field(..., description="Dados de treinamento (features e target)")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class LogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Evento de inicialização
@app.on_event("startup")
async def startup_event():
    # Inicializar o banco de dados
    init_db()
    logger.info("Banco de dados inicializado")
    
    # Verificar se existe um usuário admin
    db = next(get_db())
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        # Criar usuário admin
        admin = User(
            email="admin@example.com",
            username="admin",
            full_name="Administrador",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        logger.info("Usuário admin criado")
    
    # Criar diretório para modelos se não existir
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)
    logger.info("Diretório de modelos verificado")

# Endpoint para login de usuário
@app.post("/api/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Registrar login
    log_action(db, user.id, "login", {"method": "form"}, None)
    
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint para registrar um novo usuário
@app.post("/api/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # Verificar se o email já existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Verificar se o username já existe
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe"
        )
    
    # Criar novo usuário
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        is_active=True,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Registrar criação de usuário
    log_action(db, db_user.id, "user_created", {}, None)
    
    return db_user

# Endpoint para obter detalhes do usuário atual
@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user

# Endpoint para atualizar usuário atual
@app.put("/api/users/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Atualizar campos do usuário
    if user_update.email is not None:
        # Verificar se o email já existe
        db_user = db.query(User).filter(User.email == user_update.email).first()
        if db_user and db_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já registrado"
            )
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    # Salvar alterações
    db.commit()
    db.refresh(current_user)
    
    # Registrar atualização
    log_action(db, current_user.id, "user_updated", {}, None)
    
    return current_user

# Endpoint para fazer uma previsão
@app.post("/api/predictions", response_model=PredictionResponse)
async def create_prediction(
    prediction_request: PredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Obter o modelo
        model = get_model(
            model_type=prediction_request.prediction_type,
            model_name="default"
        )
        
        # Converter input_data para DataFrame
        input_df = pd.DataFrame([prediction_request.input_data])
        
        # Verificar se o modelo está treinado
        if not model.is_trained:
            # Treinar com dados fictícios se não houver modelo treinado
            # Em um caso real, isso não deveria acontecer, mas é útil para demonstração
            if prediction_request.prediction_type == "classifier":
                X_train = pd.DataFrame({
                    'feature1': [1, 2, 3, 4, 5],
                    'feature2': [5, 4, 3, 2, 1]
                })
                y_train = pd.Series(['A', 'B', 'A', 'B', 'A'], name='target')
            else:  # regressor
                X_train = pd.DataFrame({
                    'feature1': [1, 2, 3, 4, 5],
                    'feature2': [5, 4, 3, 2, 1]
                })
                y_train = pd.Series([10, 20, 30, 40, 50], name='target')
                
            model.train(X_train, y_train)
            model.save()
        
        # Fazer previsão
        prediction_result = model.predict(input_df)
        
        # Para classificação, adicionar probabilidades se disponível
        output_data = {}
        if prediction_request.prediction_type == "classifier":
            # Converter resultado para tipo serializável
            if isinstance(prediction_result, np.ndarray):
                prediction_class = prediction_result[0]
                if not isinstance(prediction_class, (str, int, float, bool)):
                    prediction_class = prediction_class.item()
                
                output_data["class"] = prediction_class
                
                # Adicionar probabilidades se possível
                try:
                    proba = model.predict_proba(input_df)[0].tolist()
                    output_data["probabilities"] = proba
                    output_data["class_names"] = model.label_encoders['target'].classes_.tolist()
                except:
                    pass
            else:
                output_data["class"] = prediction_result
        else:  # regressor
            # Converter resultado para tipo serializável
            if isinstance(prediction_result, np.ndarray):
                prediction_value = prediction_result[0]
                if not isinstance(prediction_value, (str, int, float, bool)):
                    prediction_value = float(prediction_value)
                
                output_data["value"] = prediction_value
            else:
                output_data["value"] = float(prediction_result)
        
        # Criar registro de previsão
        db_prediction = Prediction(
            user_id=current_user.id,
            prediction_type=prediction_request.prediction_type,
            input_data=prediction_request.input_data,
            output_data=output_data
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        # Registrar previsão
        log_action(
            db, 
            current_user.id, 
            "prediction_created", 
            {"prediction_id": db_prediction.id, "prediction_type": prediction_request.prediction_type}, 
            None
        )
        
        return db_prediction
    
    except Exception as e:
        logger.error(f"Erro ao fazer previsão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar previsão: {str(e)}"
        )

# Endpoint para obter previsões do usuário atual
@app.get("/api/predictions", response_model=List[PredictionResponse])
async def read_predictions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(
        Prediction.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return predictions

# Endpoint para treinar um modelo
@app.post("/api/models/train")
async def train_model(
    train_request: TrainRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Verificar se os dados de treinamento são válidos
        if not train_request.training_data or "features" not in train_request.training_data or "target" not in train_request.training_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados de treinamento inválidos. É necessário fornecer 'features' e 'target'."
            )
        
        # Converter dados de treinamento para DataFrames
        features_data = train_request.training_data["features"]
        target_data = train_request.training_data["target"]
        
        if not features_data or not target_data or len(features_data) != len(target_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados de treinamento inválidos. 'features' e 'target' devem ter o mesmo comprimento."
            )
        
        # Verificar se features_data é uma lista de dicionários
        if not all(isinstance(x, dict) for x in features_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados de features devem ser uma lista de objetos."
            )
        
        # Criar DataFrames
        X_train = pd.DataFrame(features_data)
        y_train = pd.Series(target_data, name="target")
        
        # Obter o modelo
        model = get_model(
            model_type=train_request.model_type,
            model_name=train_request.model_name
        )
        
        # Treinar o modelo
        metrics = model.train(X_train, y_train)
        
        # Salvar o modelo
        model_path = model.save()
        
        # Registrar treinamento
        log_action(
            db, 
            current_user.id, 
            "model_trained", 
            {
                "model_type": train_request.model_type, 
                "model_name": train_request.model_name,
                "metrics": metrics,
                "model_path": model_path
            }, 
            None
        )
        
        return {
            "message": "Modelo treinado com sucesso",
            "model_type": train_request.model_type,
            "model_name": train_request.model_name,
            "metrics": metrics,
            "model_path": model_path
        }
    
    except Exception as e:
        logger.error(f"Erro ao treinar modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao treinar modelo: {str(e)}"
        )

# Endpoint para obter métricas do modelo
@app.get("/api/models/{model_type}/{model_name}/metrics")
async def get_model_metrics(
    model_type: str,
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Obter o modelo
        model = get_model(model_type=model_type, model_name=model_name)
        
        if not model.is_trained:
            return {"message": "Modelo não treinado", "metrics": {}}
        
        return {"metrics": model.metrics}
    
    except Exception as e:
        logger.error(f"Erro ao obter métricas do modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter métricas do modelo: {str(e)}"
        )

# Endpoint para obter logs do usuário atual
@app.get("/api/logs", response_model=List[LogResponse])
async def read_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logs = db.query(Log).filter(
        Log.user_id == current_user.id
    ).order_by(
        Log.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return logs

# Endpoint para obter todos os logs (somente admin)
@app.get("/api/admin/logs", response_model=List[LogResponse])
async def read_all_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    logs = db.query(Log).order_by(
        Log.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return logs

# Endpoint para listar todos os usuários (somente admin)
@app.get("/api/admin/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# Endpoint para obter estatísticas básicas
@app.get("/api/stats")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Contagem de previsões do usuário
    prediction_count = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).count()
    
    # Contagem de logs do usuário
    log_count = db.query(Log).filter(
        Log.user_id == current_user.id
    ).count()
    
    # Estatísticas adicionais
    stats = {
        "user_id": current_user.id,
        "username": current_user.username,
        "prediction_count": prediction_count,
        "log_count": log_count,
        "account_age_days": (datetime.now() - current_user.created_at).days,
    }
    
    # Para admin, adicionar estatísticas globais
    if current_user.is_admin:
        total_users = db.query(User).count()
        total_predictions = db.query(Prediction).count()
        total_logs = db.query(Log).count()
        
        stats.update({
            "total_users": total_users,
            "total_predictions": total_predictions,
            "total_logs": total_logs,
        })
    
    return stats

# Endpoint raiz
@app.get("/")
async def root():
    return {
        "message": "API de Previsões com ML",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

# Ponto de entrada
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 