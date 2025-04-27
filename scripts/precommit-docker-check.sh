#!/bin/bash

# Determine if we're using docker or podman
DOCKER_CMD=$(command -v podman >/dev/null 2>&1 && echo "podman" || echo "docker")

# Check if the container is running
if ! $DOCKER_CMD ps | grep -q chronicler-backend; then
    echo "🐳 Container 'chronicler-backend' is not running."
    echo "Run 'make docker-up' to start the containers before committing."
    
    # Ask if the user wants to start the container
    read -p "Would you like to start the container now? [y/N] " start_container
    if [[ "$start_container" =~ ^[Yy]$ ]]; then
        echo "Starting containers with $DOCKER_CMD..."
        make docker-up
        echo "Containers started successfully!"
        exit 0
    else
        echo "Exiting without running pre-commit hooks."
        echo "You can use 'git commit --no-verify' to bypass pre-commit hooks."
        exit 1
    fi
fi

echo "✅ Container 'chronicler-backend' is running with $DOCKER_CMD."
exit 0