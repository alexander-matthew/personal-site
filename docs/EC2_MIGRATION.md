# EC2 Migration Status

Migration from Heroku to AWS EC2 with Docker Compose + nginx + Let's Encrypt.

## Completed

- [x] **Dockerfile** — python:3.11-slim + uv, uvicorn with `--proxy-headers`
- [x] **.dockerignore** — excludes .venv, .git, tests, infra, etc.
- [x] **docker-compose.yml** — web + nginx + certbot services
- [x] **nginx/default.conf.template** — HTTP→HTTPS redirect, reverse proxy to web:8000
- [x] **init-letsencrypt.sh** — Bootstrap Let's Encrypt certs from .env
- [x] **infra/main.tf** — EC2 t3.micro, security group, elastic IP, 30GB gp3 volume
- [x] **infra/variables.tf** — domain, secrets, SSH key path, region, instance type
- [x] **infra/outputs.tf** — elastic_ip, ssh_command, next_steps
- [x] **infra/terraform.tfvars.example** — template with all variables
- [x] **deploy.sh** — reads Terraform outputs, rsyncs to EC2, writes .env, deploys
- [x] **.github/workflows/deploy.yml** — replaced Heroku push with SSH deploy (appleboy/ssh-action)
- [x] **.gitignore** — added certbot/, infra state/tfvars entries
- [x] **Removed Procfile** — Heroku-specific, replaced by Docker CMD
- [x] **Removed requirements.txt** — Heroku-specific, Docker uses `uv sync --frozen`
- [x] **Updated CLAUDE.md** — EC2/Docker architecture, removed Heroku references
- [x] **Updated ARCHITECTURE.md** — new system diagram with nginx/Docker layer
- [x] **Generated SSH key** — `~/.ssh/personal-site-cert` (ed25519)
- [x] **Created terraform.tfvars** — with placeholder domain, real secret key
- [x] **Set GitHub secret** — `EC2_USER=ec2-user`

## In Progress

- [ ] **Terraform apply** — provisioning EC2 instance (waiting for completion)

## Remaining Steps

1. Note the Elastic IP from `terraform output elastic_ip`
2. Run `./deploy.sh` from WSL to sync files and start Docker on EC2
3. Set remaining GitHub secrets:
   ```bash
   gh secret set EC2_HOST --repo alexander-matthew/personal-site   # paste Elastic IP
   gh secret set EC2_SSH_KEY --repo alexander-matthew/personal-site < ~/.ssh/personal-site-cert
   ```
4. Get a domain and point DNS A record to Elastic IP
5. Update `infra/terraform.tfvars` with real domain, re-run `./deploy.sh`
6. Update Spotify redirect URI in Spotify Developer Dashboard to `https://yourdomain.com/projects/spotify/callback`
7. Add Spotify client ID/secret to `infra/terraform.tfvars`, re-run `./deploy.sh`

## Architecture

```
Browser → nginx (HTTPS) → uvicorn (FastAPI) → External APIs
                ↕
         certbot (Let's Encrypt auto-renewal)
```

All three services run as Docker Compose on a single EC2 t3.micro (Amazon Linux 2023).
