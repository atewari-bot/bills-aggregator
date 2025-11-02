.PHONY: build up down restart logs clean dev-build dev-up dev-down

# Production commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Development commands
dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up

dev-down:
	docker-compose -f docker-compose.dev.yml down

# Build and start production
start: build up

# Start development
start-dev: dev-build dev-up

