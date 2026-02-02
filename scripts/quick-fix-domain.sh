#!/bin/bash
# Quick fix script for nepalelection.subsy.tech domain issues

set -e  # Exit on error

DOMAIN="nepalelection.subsy.tech"
IP="165.22.215.152"

echo "=========================================="
echo "Quick Fix Script for $DOMAIN"
echo "=========================================="
echo ""

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run with sudo: sudo $0"
        exit 1
    fi
}

# Function to install Nginx if not present
install_nginx() {
    echo "Checking Nginx installation..."
    if ! command -v nginx &> /dev/null; then
        echo "Installing Nginx..."
        apt-get update
        apt-get install -y nginx certbot python3-certbot-nginx
    else
        echo "✓ Nginx is already installed"
    fi
}

# Function to create Nginx config
create_nginx_config() {
    echo "Creating Nginx configuration..."
    cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";

        # Handle OPTIONS requests
        if (\$request_method = 'OPTIONS') {
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
EOF
    echo "✓ Nginx configuration created"
}

# Function to enable site
enable_site() {
    echo "Enabling Nginx site..."
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
    rm -f /etc/nginx/sites-enabled/default
    echo "✓ Site enabled"
}

# Function to test and reload Nginx
reload_nginx() {
    echo "Testing Nginx configuration..."
    if nginx -t; then
        echo "✓ Configuration is valid"
        echo "Reloading Nginx..."
        systemctl reload nginx
        echo "✓ Nginx reloaded"
    else
        echo "✗ Nginx configuration test failed"
        exit 1
    fi
}

# Function to configure firewall
configure_firewall() {
    echo "Configuring firewall..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    echo "✓ Firewall configured"
}

# Function to get SSL certificate
get_ssl() {
    echo ""
    echo "=========================================="
    echo "Obtaining SSL Certificate"
    echo "=========================================="
    echo ""
    echo "You will be prompted for:"
    echo "  - Email address (for certificate expiration notices)"
    echo "  - Agree to terms of service"
    echo "  - Choose whether to redirect HTTP to HTTPS (recommended: YES)"
    echo ""
    read -p "Press Enter to continue with SSL setup..."
    certbot --nginx -d $DOMAIN
    echo ""
    echo "✓ SSL certificate obtained and configured"
}

# Function to verify setup
verify_setup() {
    echo ""
    echo "=========================================="
    echo "Verifying Setup"
    echo "=========================================="
    echo ""

    # Check Nginx status
    if systemctl is-active --quiet nginx; then
        echo "✓ Nginx is running"
    else
        echo "✗ Nginx is NOT running"
        exit 1
    fi

    # Check if app is running
    if netstat -tuln | grep -q ":8000 "; then
        echo "✓ Application is listening on port 8000"
    else
        echo "✗ Application is NOT listening on port 8000"
        echo "  Make sure Docker is running: docker compose up -d"
    fi

    # Test HTTP
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80 || echo "000")
    if [ "$HTTP_STATUS" != "000" ]; then
        echo "✓ HTTP connection works (status: $HTTP_STATUS)"
    else
        echo "✗ HTTP connection failed"
    fi

    # Test HTTPS (if cert exists)
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:443 || echo "000")
        if [ "$HTTPS_STATUS" != "000" ]; then
            echo "✓ HTTPS connection works (status: $HTTPS_STATUS)"
        else
            echo "✗ HTTPS connection failed"
        fi
    fi
}

# Main execution
check_root
install_nginx
create_nginx_config
enable_site
reload_nginx
configure_firewall

echo ""
echo "=========================================="
echo "Basic setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify DNS: $DOMAIN should point to $IP"
echo "  2. Get SSL certificate (recommended)"
echo ""

read -p "Do you want to obtain SSL certificate now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    get_ssl
fi

verify_setup

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Your application should now be accessible at:"
echo "  - HTTP:  http://$DOMAIN"
echo "  - HTTPS: https://$DOMAIN (if SSL was configured)"
echo ""
echo "From your local machine, test with:"
echo "  curl http://$DOMAIN"
echo "  curl https://$DOMAIN"
echo ""
echo "Or open in browser:"
echo "  https://$DOMAIN"
echo ""
