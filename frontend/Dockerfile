FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

EXPOSE 7860

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "7860"]
