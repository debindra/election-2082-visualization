# Deploy to Digital Ocean Droplet

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

## 5. Production with Nginx (optional)

To serve on port 80/443 with SSL, add an Nginx reverse proxy:

```bash
apt-get install -y nginx certbot python3-certbot-nginx

# Edit /etc/nginx/sites-available/default
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
nginx -t && systemctl reload nginx
certbot --nginx -d your-domain.com  # SSL
```

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
