from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import joblib
import os
import numpy as np

from database import get_db, init_db, Feedback
from train_model import preprocess_text

# Criar a aplicação FastAPI
app = FastAPI(title="API de Classificação de Feedbacks")

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
class FeedbackRequest(BaseModel):
    text: str

# Definir o schema da resposta
class FeedbackResponse(BaseModel):
    text: str
    is_positive: bool
    confidence: float

# Definir o schema para listagem
class FeedbackDB(BaseModel):
    id: int
    text: str
    is_positive: bool
    confidence: float

    class Config:
        orm_mode = True

# Endpoint para classificação via JSON
@app.post("/classify-feedback", response_model=FeedbackResponse)
def classify_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    return _process_feedback(request.text, db)

# Endpoint para classificação via formulário (para upload de arquivo de texto)
@app.post("/upload-feedback", response_model=FeedbackResponse)
async def upload_feedback(
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    return _process_feedback(text, db)

# Endpoint para classificação via arquivo
@app.post("/upload-feedback-file", response_model=FeedbackResponse)
async def upload_feedback_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    text = content.decode('utf-8')
    return _process_feedback(text, db)

def _process_feedback(text: str, db: Session):
    """Função interna para processar e classificar o feedback."""
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="O texto do feedback não pode estar vazio")
    
    # Pré-processar o texto
    processed_text = preprocess_text(text)
    
    # Fazer a classificação
    prediction_proba = model.predict_proba([processed_text])[0]
    is_positive = bool(model.predict([processed_text])[0])
    confidence = float(prediction_proba[1] if is_positive else prediction_proba[0])
    
    # Salvar no banco de dados
    feedback = Feedback(
        text=text,
        is_positive=is_positive,
        confidence=confidence
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return {
        "text": text,
        "is_positive": is_positive,
        "confidence": confidence
    }

# Endpoint para listar feedbacks classificados
@app.get("/feedbacks", response_model=List[FeedbackDB])
def get_feedbacks(db: Session = Depends(get_db), limit: int = 100):
    return db.query(Feedback).order_by(Feedback.id.desc()).limit(limit).all()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 