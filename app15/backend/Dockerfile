FROM python:3.9-slim

WORKDIR /app

# Copiar arquivos de requisitos
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Criar pasta para modelos
RUN mkdir -p models/visualizations

# Expor a porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 