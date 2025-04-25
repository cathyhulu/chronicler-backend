#!/bin/bash

# Determine if we're using docker or podman
DOCKER_CMD=$(command -v podman >/dev/null 2>&1 && echo "podman" || echo "docker")

# Container name
CONTAINER_NAME="chronicler-backend"

# Command to run is all arguments passed to this script
COMMAND="$@"

# Check if the container is running
if ! $DOCKER_CMD ps | grep -q $CONTAINER_NAME; then
    echo "Container '$CONTAINER_NAME' is not running."
    echo "Run 'make docker-up' to start the containers before running commands."
    exit 1
fi

# Run the command in the container
$DOCKER_CMD exec -i $CONTAINER_NAME bash -c "$COMMAND"