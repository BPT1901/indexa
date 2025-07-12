#!/bin/bash

# Indexa Production Deployment Script
# Run this script to build and push the Docker image to Docker Hub

set -e

echo "🚀 Building and deploying Indexa to production..."

# Configuration
DOCKER_USER="bpt1901"
IMAGE_NAME="indexa"
TAG="latest"
FULL_IMAGE_NAME="${DOCKER_USER}/${IMAGE_NAME}:${TAG}"

echo "📦 Building Docker image: ${FULL_IMAGE_NAME}"
docker build -t ${FULL_IMAGE_NAME} .

echo "🔐 Logging into Docker Hub (you may be prompted for credentials)"
docker login

echo "⬆️  Pushing image to Docker Hub..."
docker push ${FULL_IMAGE_NAME}

echo "✅ Successfully pushed ${FULL_IMAGE_NAME} to Docker Hub"
echo ""
echo "🎯 Next steps:"
echo "1. Copy docker-compose.prod.yml and .env.production to your LXC container"
echo "2. Adjust the NAS mount path in docker-compose.prod.yml if needed"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🌐 Your app will be available at: http://your-lxc-ip:8000"