# Makefile for Receipt Processor Docker operations

# Variables
IMAGE_NAME = receipt-processor
CONTAINER_NAME = receipt-processor
PORT = 8501
VERSION = latest

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  build       - Build the Docker image"
	@echo "  run         - Run the container"
	@echo "  stop        - Stop the container"
	@echo "  clean       - Remove container and image"
	@echo "  logs        - Show container logs"
	@echo "  shell       - Open shell in running container"
	@echo "  test        - Run tests in container"
	@echo "  push        - Push image to registry"
	@echo "  dev         - Run in development mode with volume mounts"

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(VERSION) .
	docker tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

# Build with no cache
.PHONY: build-no-cache
build-no-cache:
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) .

# Run the container
.PHONY: run
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):8501 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME):$(VERSION)

# Run in development mode with source code mounted
.PHONY: dev
dev:
	docker run -it --rm \
		--name $(CONTAINER_NAME)-dev \
		-p $(PORT):8501 \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		$(IMAGE_NAME):$(VERSION)

# Stop the container
.PHONY: stop
stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Show logs
.PHONY: logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Open shell in running container
.PHONY: shell
shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Run tests
.PHONY: test
test:
	docker run --rm \
		-v $(PWD)/tests:/app/tests \
		$(IMAGE_NAME):$(VERSION) \
		python -m pytest tests/ -v

# Clean up
.PHONY: clean
clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME):$(VERSION) || true
	docker rmi $(IMAGE_NAME):latest || true

# Push to registry (customize registry URL)
.PHONY: push
push:
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

# Docker compose operations
.PHONY: up
up:
	docker-compose up -d

.PHONY: down
down:
	docker-compose down

.PHONY: restart
restart:
	docker-compose restart

# System cleanup
.PHONY: system-clean
system-clean:
	docker system prune -f
	docker volume prune -f
