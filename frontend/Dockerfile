FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG API_URL=https://datapulse-backend.onrender.com/api
RUN sed -i "s#https://datapulse-backend.onrender.com/api#${API_URL}#" src/environments/environment.ts

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
