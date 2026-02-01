# Deploy to Digital Ocean Droplet

## Quick: serve electionnepal.subsy.tech on 165.22.215.152

1. **DNS**: Point **electionnepal.subsy.tech** to **165.22.215.152** (A record). DigitalOcean/your DNS provider handles this; no extra DNS steps on the server.
2. **On the droplet**: Install Nginx, add a `server { server_name electionnepal.subsy.tech; ... proxy_pass http://127.0.0.1:8000; }` block, reload Nginx, then run `certbot --nginx -d electionnepal.subsy.tech` for HTTPS.  
   Full steps are in **Section 5** below.

---

## Prerequisites

- Digital Ocean droplet (Ubuntu 22.04 LTS recommended)
- Docker and Docker Compose installed on the droplet
- Domain (optional) or droplet IP

## 1. Prepare the droplet

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose plugin
apt-get update && apt-get install -y docker-compose-plugin
```

## 2. Clone project on droplet

On the droplet (or after SSH):

```bash
cd /opt
git clone <your-repo-url> election-visualization
cd election-visualization
```

Add your election CSVs to `data/elections/` (e.g. `2082.csv`). The GeoJSON for Nepal districts is included in the repo.

## 3. Environment variables

Create `.env` on the droplet (optional; defaults work for single-origin deployment):

```bash
# /opt/election-visualization/.env

# CORS: add your domain if frontend is on a different origin
# For same-origin (default), leave empty or use your droplet URL
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Or for droplet IP:
# CORS_ORIGINS=http://your-droplet-ip:8000
```

## 4. Build and run

**First time:**
```bash
cd /opt/election-visualization
docker compose up -d --build
```

**Subsequent deploys (use `deploy.sh`):**
```bash
cd /opt/election-visualization
./deploy.sh
```

Or manually:
```bash
git fetch --all
git pull
docker compose build
docker compose up -d
```

If building on Mac M1/ARM for an x86 droplet:
```bash
docker compose build --platform linux/amd64 && docker compose up -d
```

Check logs: `docker compose logs -f`

The app will be available at `http://your-droplet-ip:8000`.

## 5. Serve the domain (electionnepal.subsy.tech)

DNS for **electionnepal.subsy.tech** should point to your droplet IP (**165.22.215.152**). On the droplet, configure Nginx so the server responds to that hostname.

### 5a. Install Nginx and Certbot (if not already)

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 5b. Nginx site for electionnepal.subsy.tech

Create a site config (or replace the default):

```bash
sudo nano /etc/nginx/sites-available/electionnepal
```

Paste (use your domain; replace if you use a different one):

```nginx
server {
    listen 80;
    server_name electionnepal.subsy.tech;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and test:

```bash
sudo ln -sf /etc/nginx/sites-available/electionnepal /etc/nginx/sites-enabled/
# If you had default enabled and want only this domain on this server:
# sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 5c. SSL with Let's Encrypt

```bash
sudo certbot --nginx -d electionnepal.subsy.tech
```

Follow the prompts (email, agree to terms). Certbot will configure HTTPS and redirect HTTP → HTTPS.

After this, **https://electionnepal.subsy.tech** will serve your app (Nginx proxies to the app on port 8000).

### Optional: also serve by droplet IP

To keep **http://165.22.215.152:8000** working, leave the app listening on 8000 and ensure firewall allows it (see Section 6). The domain will use port 80/443 via Nginx only.

## 6. Firewall

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 8000  # or remove if using nginx only
ufw enable
```

## Useful commands

```bash
# Restart after updating code
docker compose up -d --build

# View logs
docker compose logs -f app

# Stop
docker compose down
```
