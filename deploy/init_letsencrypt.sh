#!/usr/bin/env bash
# Obtain the first Let's Encrypt certificate, then switch Nginx to HTTPS.
#
#   EMAIL=you@example.com ./deploy/init_letsencrypt.sh
#
# Prerequisite: codespher.me and www.codespher.me point (A record) at the
# EC2 Elastic IP and the stack is running with NGINX_CONF=local.conf.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${EMAIL:?set EMAIL for Let's Encrypt notices}"
DOMAINS=(-d codespher.me -d www.codespher.me)
PROJECT="${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}"
WEBROOT_VOLUME="${PROJECT}_certbot-www"

# Nginx (local.conf) already serves /.well-known/acme-challenge/ from the
# certbot-www volume, so certbot only has to write the challenge file there.
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v "$WEBROOT_VOLUME":/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  "${DOMAINS[@]}" --email "$EMAIL" --agree-tos --no-eff-email

# Switch to the HTTPS config and reload.
sed -i 's/^NGINX_CONF=.*/NGINX_CONF=codesphere.conf/' .env
NGINX_CONF=codesphere.conf docker compose up -d nginx

# Auto-renewal: add to root's crontab (sudo crontab -e):
#   0 3 * * * docker run --rm -v /etc/letsencrypt:/etc/letsencrypt -v <project>_certbot-www:/var/www/certbot certbot/certbot renew --quiet && docker compose -f /home/ubuntu/codesphere/docker-compose.yml exec nginx nginx -s reload
echo "HTTPS enabled for codespher.me"
