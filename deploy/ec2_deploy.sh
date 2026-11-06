#!/usr/bin/env bash
# Pull the latest images from ECR and (re)start the stack on EC2.
#
#   AWS_ACCOUNT_ID=123456789012 AWS_REGION=ap-south-1 ./deploy/ec2_deploy.sh [tag]
set -euo pipefail
cd "$(dirname "$0")/.."

: "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
TAG="${1:-latest}"
REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

[ -f .env ] || { echo "Create .env from .env.example first"; exit 1; }

export WEB_IMAGE="$REGISTRY/codesphere-web:$TAG"
export RUNNER_IMAGE="$REGISTRY/codesphere-runner:$TAG"
export DOCKER_GID="$(stat -c %g /var/run/docker.sock)"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

docker compose pull web runner
docker compose up -d --no-build
docker image prune -f

docker compose ps
