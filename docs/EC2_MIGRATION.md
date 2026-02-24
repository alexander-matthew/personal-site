# EC2 Deployment Runbook

This project has migrated from Heroku to AWS EC2 with Docker Compose, nginx, and Let's Encrypt.
Use this document as the current deployment checklist.

## Target Architecture

```text
Browser -> nginx (HTTPS) -> uvicorn (FastAPI) -> External APIs
                  |
                  -> certbot (Let's Encrypt renewals)
```

Services run on a single EC2 instance via `docker-compose.yml`:
- `web` (FastAPI app)
- `nginx` (reverse proxy + TLS termination)
- `certbot` (certificate renewal)

## Prerequisites

- AWS credentials configured locally
- Terraform installed
- An SSH key pair (public key path used in Terraform)
- A domain with DNS control

## 1. Provision Infrastructure

```bash
cd infra
terraform init
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your domain, email, secrets, and ssh_public_key_path
terraform apply
```

After apply:
- Note the Elastic IP: `terraform output -raw elastic_ip`
- Confirm the generated SSH command: `terraform output -raw ssh_command`

## 2. Point DNS

Create an `A` record for your domain pointing to the Elastic IP.

If using Cloudflare during initial certificate issuance, use DNS-only (no proxy) until certificates are successfully provisioned.

## 3. Deploy the Application

From repo root:

```bash
./deploy.sh
```

What `deploy.sh` does:
- Reads Terraform outputs and `infra/terraform.tfvars`
- Waits for EC2 bootstrap completion
- Syncs project files to `~/personal-site` on EC2
- Writes runtime `.env` on the server
- Runs first-time HTTPS bootstrap (`init-letsencrypt.sh`) or normal `docker compose up -d --build`

## 4. Configure GitHub Actions Deploy

Set these repository secrets:

```bash
gh secret set EC2_HOST --repo alexander-matthew/personal-site
gh secret set EC2_USER --repo alexander-matthew/personal-site
gh secret set EC2_SSH_KEY --repo alexander-matthew/personal-site < ~/.ssh/your_private_key
```

Expected values:
- `EC2_HOST`: Elastic IP or host
- `EC2_USER`: `ec2-user`
- `EC2_SSH_KEY`: private key matching the instance's authorized key

On push to `main`, workflow `.github/workflows/deploy.yml` runs:
- `git pull origin main`
- `docker compose up -d --build`

## 5. Spotify OAuth Production Settings

In the Spotify Developer Dashboard, set redirect URI to:

```text
https://<your-domain>/projects/spotify/callback
```

Ensure `spotify_client_id` and `spotify_client_secret` are set in `infra/terraform.tfvars`, then rerun `./deploy.sh`.

## Operations Notes

- App logs: `docker compose logs -f web`
- nginx logs: `docker compose logs -f nginx`
- certbot logs: `docker compose logs -f certbot`
- Rebuild/restart: `docker compose up -d --build`
