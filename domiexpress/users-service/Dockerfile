
FROM node:18-alpine

WORKDIR /app

COPY backend/package.json ./

# Instala las dependencias (express, mysql2, cors)
RUN npm install

COPY backend/ ./

EXPOSE 3000

CMD ["node", "server.js"]
