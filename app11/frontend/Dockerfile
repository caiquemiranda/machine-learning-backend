FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Configuração de produção com nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

# Arquivo de configuração para o nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 