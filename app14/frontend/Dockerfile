# Estágio de build
FROM node:18-alpine as build

WORKDIR /app

# Copiar arquivos de configuração
COPY package.json package-lock.json* ./

# Instalar dependências
RUN npm install

# Copiar código fonte
COPY . .

# Definir o URL da API para ambiente de produção
ENV REACT_APP_API_URL=http://localhost:8000

# Construir aplicativo
RUN npm run build

# Estágio de produção com Nginx
FROM nginx:alpine

# Copiar build
COPY --from=build /app/build /usr/share/nginx/html

# Copiar configuração do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta
EXPOSE 80

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"] 