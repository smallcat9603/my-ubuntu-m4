# my-ubuntu-m4
This repository contains the necessary files to automatically build and deploy the Docker image `my-ubuntu-m4` to Docker Hub.
Any change in files Dockerfile and .github/workflows/docker-image.yml will be automatically reflected in `my-ubuntu-m4` in Docker Hub.

## Files

- Dockerfile

Defines the instructions to build the `my-ubuntu-m4` Docker image.

- .github/workflows/docker-image.yml

Contains the GitHub Actions workflow for automatically building and pushing the `my-ubuntu-m4` image to Docker Hub.
(secrets.DOCKER_USERNAME and secrets.DOCKER_PASSWORD are set in Settings - Secrets and Variables - Actions)
