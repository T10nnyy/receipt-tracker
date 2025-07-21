# Docker commands for receipt processor
.PHONY: build run dev logs clean stop restart shell test

# Variables
IMAGE_NAME = receipt-processor
CONTAINER_NAME = receipt-processor-app
PORT = 8501

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run the container in production mode
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):8501 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME)

# Run in development mode with source code mounted
dev:
	docker run -it \
		--name $(CONTAINER_NAME)-dev \
		-p $(PORT):8501 \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME)

# View container logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Stop the container
stop:
	docker stop $(CONTAINER_NAME) || true
	docker stop $(CONTAINER_NAME)-dev || true

# Remove containers and images
clean: stop
	docker rm $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME)-dev || true
	docker rmi $(IMAGE_NAME) || true

# Restart the container
restart: stop run

# Get a shell inside the running container
shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Run with docker-compose
up:
	docker-compose up -d

# Stop docker-compose
down:
	docker-compose down

# View docker-compose logs
compose-logs:
	docker-compose logs -f

# Build and run with docker-compose
compose-build:
	docker-compose up --build -d

# Show container status
status:
	docker ps -a | grep $(IMAGE_NAME)

# Show image size
size:
	docker images | grep $(IMAGE_NAME)

# Prune unused Docker resources
prune:
	docker system prune -f
	docker image prune -f

# Help
help:
	@echo "Available commands:"
	@echo "  build         - Build the Docker image"
	@echo "  run           - Run container in production mode"
	@echo "  dev           - Run container in development mode"
	@echo "  logs          - View container logs"
	@echo "  stop          - Stop the container"
	@echo "  clean         - Remove containers and images"
	@echo "  restart       - Restart the container"
	@echo "  shell         - Get shell access to container"
	@echo "  up            - Start with docker-compose"
	@echo "  down          - Stop docker-compose"
	@echo "  compose-logs  - View docker-compose logs"
	@echo "  compose-build - Build and start with docker-compose"
	@echo "  status        - Show container status"
	@echo "  size          - Show image size"
	@echo "  prune         - Clean up unused Docker resources"
	@echo "  help          - Show this help message"
