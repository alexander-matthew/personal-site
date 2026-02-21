#!/bin/bash

# init-letsencrypt.sh — Bootstrap Let's Encrypt certificates
#
# Reads DOMAIN and LETSENCRYPT_EMAIL from .env so the domain
# is configured in exactly one place.
#
# Usage: chmod +x init-letsencrypt.sh && ./init-letsencrypt.sh

set -e

# Load DOMAIN and LETSENCRYPT_EMAIL from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | grep -E '^(DOMAIN|LETSENCRYPT_EMAIL)=' | xargs)
fi

if [ -z "$DOMAIN" ]; then
  echo "Error: DOMAIN is not set. Add it to your .env file."
  exit 1
fi

if [ -z "$LETSENCRYPT_EMAIL" ]; then
  echo "Error: LETSENCRYPT_EMAIL is not set. Add it to your .env file."
  exit 1
fi

domains=($DOMAIN)
email="$LETSENCRYPT_EMAIL"
staging=0  # Set to 1 to use Let's Encrypt staging (avoids rate limits while testing)
data_path="./certbot"

echo "### Setting up SSL for $DOMAIN ..."

if [ -d "$data_path/conf/live/${domains[0]}" ]; then
  read -p "Existing data found for ${domains[0]}. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# Download recommended TLS parameters
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# Create certbot webroot for ACME challenges
mkdir -p "$data_path/www"

# Create dummy certificate for nginx to start
echo "### Creating dummy certificate for ${domains[0]} ..."
cert_path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout '$cert_path/privkey.pem' \
    -out '$cert_path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Start nginx with dummy certificate
echo "### Starting nginx ..."
docker compose up --force-recreate -d nginx
echo

# Delete dummy certificate
echo "### Deleting dummy certificate for ${domains[0]} ..."
docker compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/${domains[0]} && \
  rm -rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo

# Request real certificate
echo "### Requesting Let's Encrypt certificate for ${domains[0]} ..."

# Select appropriate domain args
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select staging or production
if [ $staging != "0" ]; then
  staging_arg="--staging"
fi

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    --email $email \
    $domain_args \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot
echo

# Reload nginx with real certificate
echo "### Reloading nginx ..."
docker compose exec nginx nginx -s reload

echo "### Done! HTTPS is now configured for $DOMAIN."
