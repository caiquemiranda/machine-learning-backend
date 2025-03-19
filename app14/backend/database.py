from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# URL de conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/estimativa_atendimento_db")

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definir modelos ORM
class TipoSolicitacao(Base):
    __tablename__ = "tipos_solicitacao"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    descricao = Column(String, nullable=True)
    
    # Relacionamentos
    estimativas = relationship("Estimativa", back_populates="tipo_solicitacao")

class Estimativa(Base):
    __tablename__ = "estimativas"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_solicitacao_id = Column(Integer, ForeignKey("tipos_solicitacao.id"))
    complexidade = Column(Integer, index=True)  # 1-5, onde 5 é mais complexo
    tempo_estimado = Column(Float)  # Tempo estimado em minutos
    tempo_real = Column(Float, nullable=True)  # Tempo real (se disponível)
    data_criacao = Column(DateTime, default=datetime.now)
    observacoes = Column(String, nullable=True)
    
    # Relacionamentos
    tipo_solicitacao = relationship("TipoSolicitacao", back_populates="estimativas")

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