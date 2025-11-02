# Docker Guide

This guide explains how to run the Bills Analyzer & Aggregator using Docker.

## Quick Start

### Production Mode

```bash
# Build and start
docker-compose up --build

# Or using Makefile
make start
```

Access the application at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

### Development Mode

```bash
# Start with hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Or using Makefile
make start-dev
```

## Docker Services

### Backend Service

- **Image**: Built from `backend/Dockerfile`
- **Port**: 5000
- **Features**:
  - Python 3.11 with Flask
  - Tesseract OCR pre-installed
  - SQLite database in persistent volume
  - Uploads directory mounted as volume

### Frontend Service

- **Image**: Built from `frontend/Dockerfile`
- **Port**: 3000 (mapped to nginx port 80)
- **Features**:
  - Nginx for serving React build
  - API proxy configuration
  - Static asset caching

## Volumes

- `bills-db`: Persistent storage for SQLite database
- `./backend/uploads`: Local directory for uploaded files (mounted)

## Environment Variables

### Backend

- `FLASK_ENV`: Set to `production` in Docker, `development` in dev mode
- `DATABASE_URL`: Database connection string (default: `sqlite:///app/data/bills.db`)
- `UPLOAD_FOLDER`: Upload directory (default: `uploads`)

### Frontend

- `REACT_APP_API_URL`: Backend API URL (only for dev mode, production uses nginx proxy)

## Useful Commands

```bash
# View logs
docker-compose logs -f
docker-compose logs -f backend    # Backend logs only
docker-compose logs -f frontend   # Frontend logs only

# Stop containers
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache

# Execute command in container
docker-compose exec backend python -c "print('Hello')"
docker-compose exec frontend sh

# View container status
docker-compose ps

# Restart a service
docker-compose restart backend

# Scale services (if needed)
docker-compose up --scale backend=2
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 5000 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "3001:80"  # Change frontend port
  - "5001:5000"  # Change backend port
```

### Database Not Persisting

Ensure the volume is properly created:
```bash
docker volume ls | grep bills-db
```

If the volume doesn't exist, create it:
```bash
docker volume create bills-db
```

### OCR Not Working

The backend image includes Tesseract OCR. If OCR fails, check logs:
```bash
docker-compose logs backend
```

### Frontend Can't Connect to Backend

In production mode, the frontend proxies API requests through nginx. Ensure:
1. The nginx configuration is correct (`frontend/nginx.conf`)
2. Backend service is named `backend` in docker-compose
3. Both services are on the same Docker network

### Build Failures

Clear Docker cache and rebuild:
```bash
docker-compose build --no-cache
docker system prune -a
```

## Production Deployment

For production deployment:

1. **Update environment variables** in `docker-compose.yml`
2. **Use environment-specific configuration**
3. **Set up proper SSL/TLS** (use reverse proxy like Traefik or Nginx)
4. **Configure database backup** strategy
5. **Set resource limits** in docker-compose.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    # ... rest of config
```

## Multi-Architecture Support

The Dockerfiles are designed for Linux/amd64. For ARM (Apple Silicon, Raspberry Pi), you may need to:

```bash
# Build for specific platform
docker buildx build --platform linux/arm64 -t bills-backend ./backend
```

Or use buildx for multi-platform:
```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t bills-backend ./backend
```

