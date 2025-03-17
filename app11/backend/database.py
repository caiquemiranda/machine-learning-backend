from sqlalchemy import create_engine, Column, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/house_price_db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir modelo de dados
class HousePredict(Base):
    __tablename__ = "house_predictions"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    stories = Column(Integer, nullable=False)
    parking = Column(Integer, nullable=False)
    age = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=False)

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