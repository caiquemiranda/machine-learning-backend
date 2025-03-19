from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/diagnostic_system_db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir modelos de dados
class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    training_date = Column(DateTime, default=datetime.now)
    parameters = Column(JSON, nullable=True)
    dataset_size = Column(Integer, nullable=False)
    
class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    input_data = Column(JSON, nullable=False)
    prediction = Column(String, nullable=False)
    prediction_probability = Column(Float, nullable=False)
    model_version = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

class TrainingData(Base):
    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, index=True)
    features = Column(JSON, nullable=False)
    label = Column(String, nullable=False)
    is_used_for_training = Column(Boolean, default=False)
    added_date = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)

# Função para obter conexão com o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicializar o banco de dados
def init_db():
    Base.metadata.create_all(bind=engine) 