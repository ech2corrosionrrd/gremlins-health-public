# ---- build ----
FROM node:20-alpine AS build

WORKDIR /app

# npm ci needs the lockfile and honours it exactly, so builds are reproducible.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked into the bundle at build time. "/api" keeps the app same-origin.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---- serve ----
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
