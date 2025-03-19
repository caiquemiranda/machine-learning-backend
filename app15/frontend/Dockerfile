# Estágio de build
FROM node:18-alpine as build

WORKDIR /app

# Copiar arquivos de configuração
COPY package.json package-lock.json* ./

# Instalar dependências
RUN npm ci

# Copiar código fonte
COPY . .

# Construir aplicação
RUN npm run build

# Estágio de produção
FROM nginx:alpine

# Copiar arquivos estáticos do estágio de build
COPY --from=build /app/build /usr/share/nginx/html

# Copiar configuração do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor a porta
EXPOSE 80

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"] 