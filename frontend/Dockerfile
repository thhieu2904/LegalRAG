# ============================================
# LegalRAG Frontend - React + Vite + TypeScript
# Multi-stage build for optimized production image
# ============================================

# Stage 1: Build Stage
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm ci --include=dev --only=production=false

# Copy source code
COPY . .

# Copy Docker environment file for build
COPY .env.docker .env.production

# Build the application (vite build only, skip tsc type checking)
RUN npx vite build

# Stage 2: Production Stage with Nginx
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Simple nginx config - just serve SPA (no proxy needed)
RUN echo 'server { \
    listen 3000; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
