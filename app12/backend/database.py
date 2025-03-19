from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/feedback_classifier_db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir modelo de dados
class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    is_positive = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)

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