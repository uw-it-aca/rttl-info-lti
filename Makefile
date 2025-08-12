DOCKER_REPO?=us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/rttlinfo-lti
DOCKER_TAG?=0.0.18

docker-build:
	docker build -f ./Dockerfile --no-cache -t $(DOCKER_REPO):latest -t $(DOCKER_REPO):$(DOCKER_TAG) .

docker-push: docker-build
	docker push $(DOCKER_REPO):$(DOCKER_TAG)
	docker push $(DOCKER_REPO):latest