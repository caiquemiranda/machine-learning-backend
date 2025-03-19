from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# URL de conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/ml_previsoes_db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir modelos ORM
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    predictions = relationship("Prediction", back_populates="user")
    logs = relationship("Log", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prediction_type = Column(String, index=True)  # classificação ou regressão
    input_data = Column(JSON)  # dados de entrada em formato JSON
    output_data = Column(JSON)  # resultado da previsão em formato JSON
    created_at = Column(DateTime, default=datetime.now)
    model_version = Column(String, nullable=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="predictions")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="logs")

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para inicializar o banco de dados
def init_db():
    Base.metadata.create_all(bind=engine) 