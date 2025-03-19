from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db, User, Log

# Configurações de segurança
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Em produção, use variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuração do contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Funções de utilidade para autenticação

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera um hash para a senha."""
    return pwd_context.hash(password)

def get_user(db: Session, username: str) -> Optional[User]:
    """Obtém um usuário pelo nome de usuário."""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """Autentica um usuário."""
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token de acesso JWT."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Obtém o usuário atual a partir do token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Verifica se o usuário atual está ativo."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verifica se o usuário atual é administrador."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão de administrador necessária"
        )
    return current_user

def log_action(db: Session, user_id: Optional[int], action: str, details: Optional[str] = None, ip_address: Optional[str] = None) -> Log:
    """Registra uma ação no log."""
    log = Log(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log 