#!/bin/bash
# Domain diagnostic script for nepalelection.subsy.tech

echo "=========================================="
echo "Domain Diagnostic Report"
echo "=========================================="
echo ""

# 1. Check if Nginx is installed
echo "1. Checking if Nginx is installed..."
if command -v nginx &> /dev/null; then
    echo "✓ Nginx is installed"
    nginx -v 2>&1
else
    echo "✗ Nginx is NOT installed"
    echo "   Run: sudo apt-get install -y nginx"
    exit 1
fi
echo ""

# 2. Check Nginx status
echo "2. Checking Nginx status..."
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx is running"
    systemctl status nginx --no-pager -l | head -10
else
    echo "✗ Nginx is NOT running"
    echo "   Run: sudo systemctl start nginx"
fi
echo ""

# 3. Check Nginx configuration
echo "3. Checking Nginx configuration..."
if nginx -t 2>&1; then
    echo "✓ Nginx configuration is valid"
else
    echo "✗ Nginx configuration has errors"
    exit 1
fi
echo ""

# 4. Check if domain config exists
echo "4. Checking if domain configuration exists..."
NGINX_CONF="/etc/nginx/sites-available/nepalelection"
if [ -f "$NGINX_CONF" ]; then
    echo "✓ Domain configuration exists at $NGINX_CONF"
    echo "   Content:"
    cat "$NGINX_CONF"
else
    echo "✗ Domain configuration NOT found"
    echo "   Expected at: $NGINX_CONF"
fi
echo ""

# 5. Check if domain config is enabled
echo "5. Checking if domain configuration is enabled..."
if [ -L "/etc/nginx/sites-enabled/nepalelection" ]; then
    echo "✓ Domain configuration is enabled"
else
    echo "✗ Domain configuration is NOT enabled"
    echo "   Run: sudo ln -sf /etc/nginx/sites-available/nepalelection /etc/nginx/sites-enabled/"
fi
echo ""

# 6. Check SSL certificate
echo "6. Checking SSL certificate..."
if [ -f "/etc/letsencrypt/live/nepalelection.subsy.tech/fullchain.pem" ]; then
    echo "✓ SSL certificate exists"
    CERT_DATE=$(openssl x509 -in /etc/letsencrypt/live/nepalelection.subsy.tech/fullchain.pem -noout -enddate | cut -d= -f2)
    echo "   Expires: $CERT_DATE"
else
    echo "✗ SSL certificate NOT found"
    echo "   Run: sudo certbot --nginx -d nepalelection.subsy.tech"
fi
echo ""

# 7. Check firewall
echo "7. Checking firewall status..."
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    sudo ufw status verbose | grep -E "Status|80|443|8000" || echo "No specific port rules found"
else
    echo "UFW is not installed or not in use"
fi
echo ""

# 8. Check if app is running on port 8000
echo "8. Checking if app is running on port 8000..."
if netstat -tuln | grep -q ":8000 "; then
    echo "✓ Application is listening on port 8000"
    netstat -tuln | grep ":8000 "
else
    echo "✗ Application is NOT listening on port 8000"
    echo "   Check Docker containers: docker ps"
fi
echo ""

# 9. Check DNS resolution
echo "9. Checking DNS resolution..."
DOMAIN_IP=$(dig +short nepalelection.subsy.tech)
echo "   nepalelection.subsy.tech resolves to: $DOMAIN_IP"
if [ "$DOMAIN_IP" == "165.22.215.152" ]; then
    echo "✓ DNS is pointing to correct IP (165.22.215.152)"
else
    echo "✗ DNS is NOT pointing to correct IP (expected: 165.22.215.152)"
    echo "   Update DNS A record for nepalelection.subsy.tech to point to 165.22.215.152"
fi
echo ""

# 10. Test HTTP connection
echo "10. Testing HTTP connection to localhost:80..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 | grep -q "200\|301\|302"; then
    echo "✓ HTTP connection to localhost:80 works"
else
    echo "✗ HTTP connection to localhost:80 failed"
fi
echo ""

# 11. Check Nginx error logs
echo "11. Recent Nginx error logs:"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -20 /var/log/nginx/error.log | grep -v "worker_connections" || echo "No recent errors"
else
    echo "Error log not found"
fi
echo ""

echo "=========================================="
echo "Diagnostic complete"
echo "=========================================="
