# Domain Fix Guide for nepalelection.subsy.tech

## Problem
- ✅ Works: http://165.22.215.152:8000
- ❌ Not working: https://nepalelection.subsy.tech

## Root Cause Analysis

The issue is likely one of the following:

1. **DNS not configured** - The domain `nepalelection.subsy.tech` is not pointing to `165.22.215.152`
2. **Nginx not installed** - No reverse proxy configured
3. **Nginx not configured** - Missing server block for the domain
4. **SSL certificate missing** - No HTTPS certificate from Let's Encrypt
5. **Firewall blocking** - Ports 80/443 not open
6. **Nginx not running** - Service not started

## Quick Fix Steps

### Step 1: Run Diagnostic Script on Server

SSH into your droplet and run:

```bash
cd /opt/election-visualization
chmod +x scripts/diagnose-domain.sh
sudo ./scripts/diagnose-domain.sh
```

This will tell you exactly what's wrong.

---

## Manual Troubleshooting & Fixes

### Fix 1: Verify DNS Configuration

Check if DNS is pointing correctly:

```bash
# From your local machine
dig nepalelection.subsy.tech

# Should return: 165.22.215.152
```

**If not correct:**
- Go to your DNS provider (where subsy.tech is registered)
- Update the A record for `nepalelection.subsy.tech` to point to `165.22.215.152`
- Wait for DNS propagation (can take 5 minutes to 24 hours)

---

### Fix 2: Install and Configure Nginx

SSH into the server (165.22.215.152):

```bash
# Install Nginx
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Verify Nginx is running
sudo systemctl status nginx
```

---

### Fix 3: Create Nginx Configuration

Create the domain configuration:

```bash
sudo nano /etc/nginx/sites-available/nepalelection
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name nepalelection.subsy.tech;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";

        # Handle OPTIONS requests for CORS
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
}
```

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/nepalelection /etc/nginx/sites-enabled/

# Remove default site if it conflicts
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

### Fix 4: Configure Firewall

```bash
# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Direct app access (optional)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

---

### Fix 5: Obtain SSL Certificate (HTTPS)

```bash
# Get SSL certificate (will configure Nginx automatically)
sudo certbot --nginx -d nepalelection.subsy.tech

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)
```

After this, Nginx will be updated to:
- Listen on port 443 (HTTPS)
- Redirect HTTP (port 80) to HTTPS
- Use the SSL certificate

---

### Fix 6: Verify Application is Running

```bash
# Check if Docker container is running
cd /opt/election-visualization
docker ps

# If not running, start it
docker compose up -d

# Check logs
docker compose logs -f app
```

---

### Fix 7: Test the Setup

From the server, test locally:

```bash
# Test app directly
curl http://localhost:8000/health

# Test through Nginx (HTTP)
curl -I http://localhost:80/

# Test through Nginx (HTTPS)
curl -I https://nepalelection.subsy.tech/
```

From your local machine:

```bash
# Test HTTP
curl -I http://nepalelection.subsy.tech/

# Test HTTPS
curl -I https://nepalelection.subsy.tech/

# Or just open in browser:
# https://nepalelection.subsy.tech
```

---

## Common Issues and Solutions

### Issue: DNS not resolving

**Symptom:** `ping nepalelection.subsy.tech` fails or returns wrong IP

**Solution:**
1. Check DNS at your domain registrar
2. Verify A record points to `165.22.215.152`
3. Wait for propagation (up to 24 hours)
4. Clear DNS cache: `sudo systemd-resolve --flush-caches`

### Issue: 502 Bad Gateway

**Symptom:** Nginx runs but shows 502 error

**Solution:**
```bash
# Check if app is running
docker ps

# Check app logs
docker compose logs app

# Restart app if needed
docker compose restart app
```

### Issue: Connection refused

**Symptom:** Cannot connect to port 80/443

**Solution:**
```bash
# Check Nginx status
sudo systemctl status nginx

# Start Nginx
sudo systemctl start nginx

# Check firewall
sudo ufw status
```

### Issue: SSL certificate errors

**Symptom:** Browser shows security warning

**Solution:**
```bash
# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Check certificate details
sudo certbot certificates
```

---

## Monitoring and Logs

### Check Nginx Logs

```bash
# Access log
sudo tail -f /var/log/nginx/access.log

# Error log
sudo tail -f /var/log/nginx/error.log

# Domain-specific logs (if configured separately)
sudo tail -f /var/log/nginx/nepalelection-access.log
sudo tail -f /var/log/nginx/nepalelection-error.log
```

### Check Application Logs

```bash
cd /opt/election-visualization
docker compose logs -f app
```

---

## Expected Nginx Configuration After SSL

After running `certbot --nginx`, your Nginx config should look like:

```nginx
server {
    server_name nepalelection.subsy.tech;

    # SSL configuration
    listen [::]:443 ssl ipv6only=on;
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/nepalelection.subsy.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nepalelection.subsy.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    if ($host = nepalelection.subsy.tech) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    listen [::]:80;
    server_name nepalelection.subsy.tech;
    return 404;
}
```

---

## Summary Checklist

Use this checklist to ensure everything is configured:

- [ ] DNS A record for `nepalelection.subsy.tech` points to `165.22.215.152`
- [ ] Nginx is installed and running
- [ ] Nginx configuration file exists at `/etc/nginx/sites-available/nepalelection`
- [ ] Nginx configuration is enabled (`/etc/nginx/sites-enabled/nepalelection`)
- [ ] Application (Docker container) is running on port 8000
- [ ] Firewall allows ports 80 and 443
- [ ] SSL certificate obtained from Let's Encrypt
- [ ] HTTP redirects to HTTPS
- [ ] Application is accessible at `https://nepalelection.subsy.tech`

---

## Need Help?

If you're still having issues:

1. Run the diagnostic script and share the output
2. Check Nginx error logs: `sudo tail -50 /var/log/nginx/error.log`
3. Check application logs: `docker compose logs app`
4. Verify DNS: `dig nepalelection.subsy.tech`
5. Test connectivity: `telnet 165.22.215.152 80`
