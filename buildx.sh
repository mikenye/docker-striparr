#!/bin/sh

REPO=mikenye
IMAGE=striparr

docker context use x86_64
export DOCKER_CLI_EXPERIMENTAL="enabled"
docker buildx use homecluster

# Build & push latest
docker buildx build -t ${REPO}/${IMAGE}:latest --compress --push --platform linux/amd64,linux/arm/v7,linux/arm64 .
