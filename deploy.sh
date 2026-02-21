#!/bin/bash

# deploy.sh — Deploy the personal site to EC2
#
# Reads configuration from Terraform outputs and tfvars, syncs project files
# to the server, and starts the application.
#
# Usage: ./deploy.sh

set -e

# --- Read Terraform outputs ---

cd "$(dirname "$0")"

if [ ! -d infra/.terraform ]; then
  echo "Error: Terraform not initialized. Run 'cd infra && terraform init && terraform apply' first."
  exit 1
fi

echo "### Reading Terraform outputs ..."
ELASTIC_IP=$(cd infra && terraform output -raw elastic_ip)
SSH_KEY_PATH=$(cd infra && terraform output -raw ssh_command | grep -oP '(?<=-i )\S+')

# --- Read tfvars for .env values ---

TFVARS_FILE="infra/terraform.tfvars"
if [ ! -f "$TFVARS_FILE" ]; then
  echo "Error: $TFVARS_FILE not found."
  exit 1
fi

read_tfvar() {
  grep "^$1" "$TFVARS_FILE" | sed 's/.*=\s*"\(.*\)"/\1/'
}

DOMAIN=$(read_tfvar domain)
LETSENCRYPT_EMAIL=$(read_tfvar letsencrypt_email)
SECRET_KEY=$(read_tfvar secret_key)
SPOTIFY_CLIENT_ID=$(read_tfvar spotify_client_id)
SPOTIFY_CLIENT_SECRET=$(read_tfvar spotify_client_secret)

SSH_CMD="ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=accept-new ec2-user@$ELASTIC_IP"

# --- Wait for cloud-init to finish ---

echo "### Waiting for EC2 bootstrap to complete ..."
until $SSH_CMD "test -f /home/ec2-user/.bootstrap-complete" 2>/dev/null; do
  echo "  Still bootstrapping ... (retrying in 10s)"
  sleep 10
done
echo "  Bootstrap complete."

# --- Sync project files ---

echo "### Syncing project files to server ..."
rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'infra' \
  --exclude 'certbot' \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude 'node_modules' \
  --exclude 'tests' \
  --exclude 'docs' \
  -e "ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=accept-new" \
  ./ "ec2-user@$ELASTIC_IP:~/personal-site/"

# --- Write .env on server ---

echo "### Writing .env on server ..."
$SSH_CMD "cat > ~/personal-site/.env << ENVEOF
SECRET_KEY=$SECRET_KEY
FLASK_DEBUG=false
SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET
DOMAIN=$DOMAIN
LETSENCRYPT_EMAIL=$LETSENCRYPT_EMAIL
ENVEOF"

# --- Deploy ---

if $SSH_CMD "test -d ~/personal-site/certbot/conf/live/$DOMAIN" 2>/dev/null; then
  echo "### Existing deployment detected — redeploying ..."
  $SSH_CMD "cd ~/personal-site && docker compose down && docker compose up -d --build"
else
  echo "### First deployment — bootstrapping HTTPS certificates ..."
  $SSH_CMD "cd ~/personal-site && chmod +x init-letsencrypt.sh && ./init-letsencrypt.sh && docker compose up -d"
fi

echo ""
echo "### Done! Your site should be live at https://$DOMAIN"
echo "    (Make sure your DNS A record points $DOMAIN → $ELASTIC_IP)"
