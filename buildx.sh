#!/usr/bin/env bash

REPO=mikenye
IMAGE=striparr
PLATFORMS="linux/386,linux/amd64,linux/arm/v6,linux/arm/v7,linux/arm64"

docker context use x86_64
export DOCKER_CLI_EXPERIMENTAL="enabled"
docker buildx use homecluster

# Build & push latest
docker buildx build -t "${REPO}/${IMAGE}:latest" --compress --push --platform "${PLATFORMS}" .

# Get version
COMMITHASH="$(git log | head -1 | cut -d ' ' -f 2)"
VERSION="${COMMITHASH:0:7}"

# Build & push version specific
docker buildx build -t "${REPO}/${IMAGE}:${VERSION}" --compress --push --platform "${PLATFORMS}" .
