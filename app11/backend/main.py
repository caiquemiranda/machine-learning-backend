from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import joblib
import os
import numpy as np

from database import get_db, init_db, HousePredict

# Criar a aplicação FastAPI
app = FastAPI(title="API de Previsão de Preço de Casas")

# Permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar o modelo treinado
@app.on_event("startup")
async def startup_event():
    # Verificar se o modelo existe, se não, criar um modelo básico
    if not os.path.exists("model.joblib"):
        from train_model import train_and_save_model
        train_and_save_model()
    
    global model
    model = joblib.load("model.joblib")
    init_db()

# Definir o schema da requisição
class HousePredictRequest(BaseModel):
    area: float
    bedrooms: int
    bathrooms: int
    stories: int
    parking: int
    age: float

# Definir o schema da resposta
class HousePredictResponse(BaseModel):
    predicted_price: float

# Definir o schema para listagem
class HousePredictDB(BaseModel):
    id: int
    area: float
    bedrooms: int
    bathrooms: int
    stories: int
    parking: int
    age: float
    predicted_price: float

    class Config:
        orm_mode = True

# Endpoint para previsão
@app.post("/predict", response_model=HousePredictResponse)
def predict(request: HousePredictRequest, db: Session = Depends(get_db)):
    # Preparar os dados para previsão
    features = np.array([[
        request.area,
        request.bedrooms,
        request.bathrooms,
        request.stories,
        request.parking,
        request.age
    ]])
    
    # Fazer a previsão
    predicted_price = float(model.predict(features)[0])
    
    # Salvar os dados e a previsão no banco
    house_predict = HousePredict(
        area=request.area,
        bedrooms=request.bedrooms,
        bathrooms=request.bathrooms,
        stories=request.stories,
        parking=request.parking,
        age=request.age,
        predicted_price=predicted_price
    )
    
    db.add(house_predict)
    db.commit()
    db.refresh(house_predict)
    
    return {"predicted_price": predicted_price}

# Endpoint para listar previsões salvas
@app.get("/predictions", response_model=List[HousePredictDB])
def get_predictions(db: Session = Depends(get_db)):
    return db.query(HousePredict).all()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 