FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte
COPY . .

# Expor porta da API
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app10.main:app", "--host", "0.0.0.0", "--port", "8000"] 