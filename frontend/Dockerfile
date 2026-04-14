# Stage 1: Build
FROM node:20-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

# Set production environment variable for build
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

# Stage 2: Serve
FROM nginx:stable-alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files
COPY --from=build-stage /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
