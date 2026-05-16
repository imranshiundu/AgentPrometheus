FROM node:20-alpine AS build

WORKDIR /app

COPY dashboard/package*.json ./
RUN npm install

COPY dashboard ./

ARG VITE_APP_NAME="Workspace Runtime"
ARG VITE_API_BASE="http://localhost:8000"
ARG VITE_WS_BASE="ws://localhost:8000"
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_WS_BASE=$VITE_WS_BASE

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

EXPOSE 80
