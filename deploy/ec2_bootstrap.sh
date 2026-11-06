#!/usr/bin/env bash
# One-time setup of a fresh EC2 instance (Ubuntu 22.04/24.04 or Amazon Linux 2023).
#
#   scp -r deploy docker-compose.yml .env.example ubuntu@<ec2-ip>:~/codesphere/
#   ssh ubuntu@<ec2-ip> 'cd codesphere && sudo ./deploy/ec2_bootstrap.sh'
#
# Security group: allow 22 (your IP only), 80 and 443.
# IAM: attach an instance role with AmazonEC2ContainerRegistryReadOnly so the
#      box can pull from ECR without storing AWS keys on disk.
set -euo pipefail

if command -v apt-get >/dev/null; then
  apt-get update
  apt-get install -y ca-certificates curl unzip
  curl -fsSL https://get.docker.com | sh            # Docker Engine + compose plugin
  DEFAULT_USER=ubuntu
else
  dnf install -y docker unzip
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  DEFAULT_USER=ec2-user
fi
systemctl enable --now docker
usermod -aG docker "${SUDO_USER:-$DEFAULT_USER}"

# AWS CLI v2 (for the ECR login)
if ! command -v aws >/dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp && /tmp/aws/install
fi

# Shared directory for sandbox work dirs (same path on host and in the web
# container), owned by the web container's non-root user (uid 1000).
mkdir -p /var/lib/codesphere/runs
chown 1000:1000 /var/lib/codesphere/runs
chmod 755 /var/lib/codesphere/runs

# Small swap file so compilers don't OOM a t2.micro/t3.micro.
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "Done. Log out and back in (docker group), then run deploy/ec2_deploy.sh"
