#!/bin/bash

# === Configuration ===
IMAGE="registry.gitlab.com/uhthesis/bidshopping/ci-base:latest"

# === Build & Push ===
echo "🔄 Building Docker image: $IMAGE"
docker build -f Dockerfile -t "$IMAGE" .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "🚀 Pushing image to GitLab registry"
docker push "$IMAGE"

if [ $? -eq 0 ]; then
    echo "✅ Image pushed successfully!"
else
    echo "❌ Failed to push image"
fi
