FROM python:3.10-slim

WORKDIR /app

# Instalar dependências de compilação para pacotes como psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Criar diretórios necessários
RUN mkdir -p models plots

# Copiar o código
COPY . .

# Expor a porta do servidor
EXPOSE 8000

# Comando para executar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 