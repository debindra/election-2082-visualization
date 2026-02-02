# Domain Troubleshooting Summary

## Issue
**Problem:** The application works on the IP address but not on the domain
- ✅ Working: http://165.22.215.152:8000
- ❌ Not working: https://nepalelection.subsy.tech

## Root Cause
The domain `nepalelection.subsy.tech` is not properly configured with a reverse proxy. The application runs on port 8000, but web browsers expect HTTPS (port 443) which needs to be handled by Nginx.

## Solution Options

### Option 1: Quick Automated Fix (Recommended)

Run the automated script on your server:

```bash
# SSH into your server
ssh root@165.22.215.152

# Navigate to project
cd /opt/election-visualization

# Run quick fix script
sudo ./scripts/quick-fix-domain.sh
```

This will automatically:
- Install Nginx if needed
- Create and enable the domain configuration
- Configure firewall
- Obtain SSL certificate (with your permission)
- Verify the setup

### Option 2: Manual Fix

Follow the step-by-step guide in `nginx-fix-guide.md` which covers:
1. DNS configuration
2. Nginx installation
3. Creating Nginx configuration
4. SSL certificate setup
5. Firewall configuration
6. Verification steps

### Option 3: Diagnostic First

Run the diagnostic script to identify what's missing:

```bash
# SSH into your server
ssh root@165.22.215.152

# Navigate to project
cd /opt/election-visualization

# Run diagnostic
sudo ./scripts/diagnose-domain.sh
```

This will check all components and tell you exactly what needs to be fixed.

## Files Created

1. **scripts/diagnose-domain.sh** - Diagnostic script to identify issues
2. **scripts/quick-fix-domain.sh** - Automated fix script
3. **scripts/README.md** - Documentation for the scripts
4. **nginx-fix-guide.md** - Comprehensive troubleshooting guide
5. **DOMAIN_TROUBLESHOOTING.md** - This summary

## What Needs to Be Configured

For the domain to work, you need:

1. **DNS** - A record pointing `nepalelection.subsy.tech` → `165.22.215.152`
2. **Nginx** - Installed and running on the server
3. **Nginx Configuration** - Server block for the domain that proxies to port 8000
4. **SSL Certificate** - From Let's Encrypt for HTTPS
5. **Firewall** - Ports 80 and 443 open
6. **Application** - Running on port 8000

## Expected Architecture After Fix

```
User Browser
    ↓
https://nepalelection.subsy.tech:443
    ↓
Nginx (handles SSL and reverse proxy)
    ↓
http://127.0.0.1:8000 (FastAPI app in Docker)
    ↓
Election Data Application
```

## Quick Verification Commands

From your local machine:

```bash
# Check DNS
dig nepalelection.subsy.tech

# Test HTTP
curl -I http://nepalelection.subsy.tech

# Test HTTPS
curl -I https://nepalelection.subsy.tech

# Or just open in browser:
# https://nepalelection.subsy.tech
```

From the server:

```bash
# Check Nginx status
sudo systemctl status nginx

# Check app status
docker ps

# Test Nginx locally
curl http://localhost:80
curl https://localhost:443
```

## Common Issues

### Issue: DNS not pointing to correct IP
**Fix:** Update A record at your domain registrar to `165.22.215.152`

### Issue: 502 Bad Gateway
**Fix:** Ensure Docker container is running: `docker compose up -d`

### Issue: Connection refused
**Fix:** Start Nginx: `sudo systemctl start nginx`

### Issue: SSL certificate errors
**Fix:** Renew certificate: `sudo certbot renew`

## Next Steps

1. **Choose your approach:** Quick fix (recommended) or manual setup
2. **Run the appropriate script** on the server
3. **Verify** that the domain works
4. **Test** from your local machine

## Need Help?

If issues persist after running the scripts:

1. Check Nginx error logs: `sudo tail -50 /var/log/nginx/error.log`
2. Check application logs: `docker compose logs app`
3. Run diagnostic script: `sudo ./scripts/diagnose-domain.sh`
4. Verify DNS is correct at your domain registrar

## Expected Result

After successful configuration:
- ✅ http://165.22.215.152:8000 - Direct access to app (still works)
- ✅ https://nepalelection.subsy.tech - HTTPS access through Nginx (newly works)
- ✅ http://nepalelection.subsy.tech - Redirects to HTTPS (newly works)
