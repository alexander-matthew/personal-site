#!/bin/bash
# deploy-homelab.sh — Build and (re)deploy on the homelab host via Cloudflare Tunnel.
#
# Usage: ./deploy-homelab.sh
#
# Pre-reqs (one-time):
#   - .env populated (see .env.homelab.example)
#   - Cloudflare tunnel created and hostname mapped to http://web:8000
#     (see infra/homelab/README.md)

set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "Error: .env not found. Copy .env.homelab.example to .env and fill it in."
  exit 1
fi

if ! grep -q '^CLOUDFLARE_TUNNEL_TOKEN=..*' .env; then
  echo "Error: CLOUDFLARE_TUNNEL_TOKEN not set in .env."
  echo "See infra/homelab/README.md for how to create a tunnel and grab the token."
  exit 1
fi

echo "### Building and starting personal-site (homelab) ..."
docker compose -f docker-compose.homelab.yml up -d --build

echo
echo "### Status:"
docker compose -f docker-compose.homelab.yml ps

echo
echo "### Tail logs with:"
echo "  docker compose -f docker-compose.homelab.yml logs -f"
