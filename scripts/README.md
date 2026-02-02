# Domain Troubleshooting Scripts

This directory contains scripts to help diagnose and fix domain issues for `nepalelection.subsy.tech`.

## Problem
- ✅ Working: http://165.22.215.152:8000
- ❌ Not working: https://nepalelection.subsy.tech

## Quick Start

### Option 1: Quick Fix (Recommended for Most Cases)

Run this script to automatically fix most common issues:

```bash
# On the server (165.22.215.152)
cd /opt/election-visualization
sudo ./scripts/quick-fix-domain.sh
```

This script will:
- Install Nginx if not present
- Create Nginx configuration for the domain
- Enable the site
- Configure firewall
- Obtain SSL certificate (optional)
- Verify the setup

### Option 2: Diagnostic First

If you want to diagnose the issue first:

```bash
# On the server
cd /opt/election-visualization
sudo ./scripts/diagnose-domain.sh
```

This will check:
- Nginx installation and status
- Domain configuration
- SSL certificate
- Firewall settings
- Application status
- DNS resolution

## Manual Fixes

See the comprehensive guide: `../nginx-fix-guide.md`

## Common Issues

### 1. DNS Not Configured
**Symptom:** `dig nepalelection.subsy.tech` returns wrong IP

**Fix:** Update DNS A record at your domain registrar to point to `165.22.215.152`

### 2. Nginx Not Installed
**Symptom:** `nginx: command not found`

**Fix:** `sudo apt-get install -y nginx`

### 3. No Nginx Configuration
**Symptom:** `/etc/nginx/sites-available/nepalelection` doesn't exist

**Fix:** Run `sudo ./scripts/quick-fix-domain.sh` or follow the manual guide

### 4. No SSL Certificate
**Symptom:** Browser shows security warning for HTTPS

**Fix:** `sudo certbot --nginx -d nepalelection.subsy.tech`

### 5. Firewall Blocking Ports
**Symptom:** Connection refused

**Fix:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Verification

After fixing, verify from your local machine:

```bash
# Check DNS
dig nepalelection.subsy.tech

# Test HTTP
curl -I http://nepalelection.subsy.tech

# Test HTTPS
curl -I https://nepalelection.subsy.tech
```

Or open in browser: https://nepalelection.subsy.tech

## Logs

### Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Application Logs
```bash
cd /opt/election-visualization
docker compose logs -f app
```

## Expected Architecture

```
Internet
    ↓
https://nepalelection.subsy.tech:443 (Nginx + SSL)
    ↓
Nginx reverse proxy (ports 80/443)
    ↓
http://127.0.0.1:8000 (Your FastAPI app)
    ↓
Docker container
```

## Files in This Directory

- `diagnose-domain.sh` - Diagnostic script to identify issues
- `quick-fix-domain.sh` - Automated fix script
- `README.md` - This file

## Related Documentation

- `../nginx-fix-guide.md` - Comprehensive guide with manual steps
- `../DEPLOYMENT.md` - Full deployment documentation

## Support

If you're still having issues after running these scripts:

1. Check Nginx error logs: `sudo tail -50 /var/log/nginx/error.log`
2. Check application logs: `docker compose logs app`
3. Run diagnostic script and share the output
4. Ensure DNS is properly configured at your domain registrar
