#!/usr/bin/env bash
# Build the web + runner images and push them to Amazon ECR.
# Run from your laptop or CI.
#
#   AWS_ACCOUNT_ID=123456789012 AWS_REGION=ap-south-1 ./deploy/ecr_push.sh [tag]
#
# Needs: docker, aws CLI v2 configured with ecr:* permissions.
set -euo pipefail

: "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
TAG="${1:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}"
REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 1. Create the repositories once (no-op if they exist).
for repo in codesphere-web codesphere-runner; do
  aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1 \
    || aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION" \
         --image-scanning-configuration scanOnPush=true >/dev/null
done

# 2. Log Docker in to ECR (token is valid for 12 hours).
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

# 3. Build for the EC2 architecture and push both images.
PLATFORM="${PLATFORM:-linux/amd64}"
docker build --platform "$PLATFORM" -t "$REGISTRY/codesphere-web:$TAG" "$ROOT/backend"
docker build --platform "$PLATFORM" -t "$REGISTRY/codesphere-runner:$TAG" -f "$ROOT/sandbox/Dockerfile" "$ROOT"

for repo in codesphere-web codesphere-runner; do
  docker tag "$REGISTRY/$repo:$TAG" "$REGISTRY/$repo:latest"
  docker push "$REGISTRY/$repo:$TAG"
  docker push "$REGISTRY/$repo:latest"
done

echo "Pushed $REGISTRY/codesphere-{web,runner}:$TAG"
