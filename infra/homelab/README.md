# Homelab deployment (Cloudflare Tunnel)

This is the **homelab** path: personal-site running on `homelab` (the MSI
Ubuntu box on the home LAN), exposed to the public internet via Cloudflare
Tunnel. No router port-forwarding, no Let's Encrypt locally, no public IP
exposed.

The future AWS/EC2 path lives in `../../infra/` (Terraform) and uses the
root `docker-compose.yml` (nginx + certbot). Both paths can coexist in this
repo.

## Architecture

```
internet ─── Cloudflare edge ─── (outbound TLS) ─── cloudflared (container)
                                                          │
                                                          ▼ (docker network)
                                                       web:8000
                                                  (FastAPI / uvicorn)
```

- `cloudflared` makes an **outbound** persistent connection to Cloudflare.
  Nothing inbound to the homelab is opened — `ufw` stays in its current
  `deny incoming` default, and no router port-forward is needed.
- Cloudflare terminates TLS at the edge using a Cloudflare-managed cert.
  The origin (cloudflared) speaks plain HTTP to `web:8000` over the
  internal docker network.
- The home IP address is **never** advertised in DNS. Cloudflare proxies
  every request.

## One-time setup

### 1. Add the domain to Cloudflare (skip if already done)

In the Cloudflare dashboard, add the domain you'll use for the site and
change its nameservers to the ones Cloudflare assigns. Wait for
propagation. (You said you already have a Cloudflare account; this step is
just adding the zone if you haven't.)

### 2. Create the tunnel

[Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/) →
**Networks** → **Tunnels** → **Create a tunnel**.

- Connector: **Cloudflared**
- Name: `homelab-personal-site` (or anything memorable)
- On the next screen, ignore the "install connector" commands — we run
  cloudflared inside docker. **Copy the token** shown in those install
  commands (the long string after `--token`). That string is your
  `CLOUDFLARE_TUNNEL_TOKEN`.

### 3. Map a public hostname to the local service

Still in the tunnel's config page:

- **Public Hostnames** → **Add a public hostname**
  - Subdomain + Domain: e.g. `www.alexandermatthew.com`
  - Service: **HTTP** → `web:8000`
    (`web` is the docker-compose service name; cloudflared resolves it on
    the internal network.)
- Save.

Cloudflare automatically creates the DNS record (a proxied CNAME) for that
hostname. No manual DNS work needed.

### 4. Populate `.env` on the host

```sh
cd ~/code/personal-site
cp .env.homelab.example .env
chmod 600 .env
# Edit .env and paste the tunnel token + Spotify creds.
```

### 5. First deploy

```sh
./deploy-homelab.sh
```

This builds the image and brings the stack up. Watch logs with:

```sh
docker compose -f docker-compose.homelab.yml logs -f
```

`cloudflared` will log `Registered tunnel connection` four times (once per
Cloudflare PoP) — that means the tunnel is live.

### 6. Boot persistence (systemd)

So the stack comes back up after a reboot:

```sh
sudo cp infra/homelab/personal-site.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable personal-site.service
sudo systemctl start personal-site.service
```

Check status / logs:

```sh
systemctl status personal-site.service
journalctl -u personal-site.service -f
```

## Day-to-day

| Task | Command |
| --- | --- |
| Redeploy after code change | `./deploy-homelab.sh` |
| Tail logs | `docker compose -f docker-compose.homelab.yml logs -f` |
| Tail just the app | `docker compose -f docker-compose.homelab.yml logs -f web` |
| Tail just the tunnel | `docker compose -f docker-compose.homelab.yml logs -f cloudflared` |
| Stop the stack | `sudo systemctl stop personal-site.service` |
| Start the stack | `sudo systemctl start personal-site.service` |
| Disable auto-start | `sudo systemctl disable personal-site.service` |

## Security posture

- **No open inbound ports.** `ufw status` should still show only `OpenSSH`
  and `in on tailscale0`. The tunnel is outbound-only.
- **Origin IP hidden.** DNS resolves the site to Cloudflare IPs, not your
  home IP.
- **TLS at the edge.** Cloudflare manages the cert; you can't get a TLS
  vulnerability locally because there's no local TLS endpoint.
- **Optional hardening you can layer on later in the Cloudflare dashboard:**
  - **WAF rules** (free tier includes managed rules).
  - **Cloudflare Access** to put SSO/email-OTP in front of paths like
    `/admin` if you ever add them.
  - **Bot fight mode**, **rate limiting** (limited free), **page rules**
    forcing HTTPS.
  - **mTLS** between cloudflared and your origin if you ever expose
    `web` on a real port (currently unnecessary — origin is on a private
    docker network only cloudflared can reach).

## Troubleshooting

**Site returns 502 from Cloudflare.** Almost always means cloudflared can
reach Cloudflare but can't reach `web:8000`. Check:

```sh
docker compose -f docker-compose.homelab.yml ps
docker compose -f docker-compose.homelab.yml logs web | tail -50
```

**`cloudflared` logs "Unauthorized" or "Failed to fetch tunnel".**
The token in `.env` is wrong or the tunnel was deleted in the dashboard.
Recreate the tunnel or copy a fresh token.

**Hostname returns "DNS_PROBE_FINISHED_NXDOMAIN".** The public hostname
wasn't added in step 3, or Cloudflare hasn't created the CNAME yet (wait
~30s after adding).

**The service doesn't come up after reboot.** `journalctl -u
personal-site.service -b` to see the failure. Most common cause is the
docker daemon hadn't finished starting; the unit waits on `docker.service`
but rebuilding the image at boot can hit registry-network races. Re-run
`sudo systemctl restart personal-site.service` and it should converge.

## Porting to AWS later

When you're ready to move to EC2 (mirroring `wedding-site`):

1. The root `docker-compose.yml` + `nginx/` + `init-letsencrypt.sh` +
   `infra/` (Terraform) are the EC2 path and are still wired up.
2. Run `cd infra && terraform init && terraform apply`, then
   `./deploy.sh` (existing script).
3. Decide whether you want to keep using Cloudflare in front of EC2 (you
   can: just point the orange-cloud CNAME at the Elastic IP instead of
   running a tunnel). The tunnel path here is purely the homelab
   convenience — there's no reason it has to survive the migration.
