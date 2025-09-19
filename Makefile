DOCKER_REPO?=us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/rttlinfo-lti
DOCKER_TAG?=0.0.26

.PHONY: help docker-build docker-push

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

docker-build: ## Build Docker image for deployment
	docker build -f ./Dockerfile --target app-container --no-cache -t $(DOCKER_REPO):latest -t $(DOCKER_REPO):$(DOCKER_TAG) .

docker-push: docker-build ## Build and push Docker image to registry
	docker push $(DOCKER_REPO):$(DOCKER_TAG)
	docker push $(DOCKER_REPO):latest