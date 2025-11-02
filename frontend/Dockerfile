# Multi-stage build for React app
FROM node:18-alpine as build

WORKDIR /app

# Copy package files and npmrc
COPY package.json .npmrc* ./

# Install dependencies
# The .npmrc file sets legacy-peer-deps=true
# postinstall script will fix ajv compatibility issues
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

