#!/bin/bash
# TradeMaster Tencent Cloud Deploy Script
# Usage: bash deploy.sh [server_ip] [your_domain.com]

set -e

SERVER_IP="${1:-}"
DOMAIN="${2:-}"

if [ -z "$SERVER_IP" ]; then
    echo "Usage: bash deploy.sh <server_ip> [your_domain.com]"
    echo "Example: bash deploy.sh 123.45.67.89 trade.example.com"
    exit 1
fi

echo "========================================"
echo " TradeMaster Deploy to $SERVER_IP"
echo "========================================"

# Step 1: SSH into server and install dependencies
echo "[1/6] Installing system dependencies..."
ssh root@$SERVER_IP "apt update && apt install -y python3 python3-pip python3-venv nginx git"

# Step 2: Create project directory
echo "[2/6] Setting up project directory..."
ssh root@$SERVER_IP "mkdir -p /var/www/trademaker /var/log/trademaker && chown -R www-data:www-data /var/www/trademaker /var/log/trademaker"

# Step 3: Clone repo
echo "[3/6] Cloning repository..."
ssh root@$SERVER_IP "cd /var/www/trademaker && git clone https://github.com/Jack-lei-prog/trademaker.git . || (cd /var/www/trademaker && git pull)"

# Step 4: Create .env (copy manually - contains secrets)
echo "[4/6] Uploading .env and deploying service files..."
echo "       Please ensure .env is configured with SECRET_KEY and LLM_API_KEY"

# Step 5: Setup Python venv and install dependencies
echo "[5/6] Setting up Python environment..."
ssh root@$SERVER_IP "cd /var/www/trademaker && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"

# Step 6: Copy service files and start
echo "[6/6] Configuring nginx and systemd..."
# Copy service file
ssh root@$SERVER_IP "cat > /etc/systemd/system/trademaker.service" < trademaker.service
# Copy nginx config
if [ -n "$DOMAIN" ]; then
    sed "s/YOUR_DOMAIN_OR_IP/$DOMAIN/" trademaker.nginx.conf | ssh root@$SERVER_IP "cat > /etc/nginx/sites-available/trademaker"
else
    sed "s/YOUR_DOMAIN_OR_IP/$SERVER_IP/" trademaker.nginx.conf | ssh root@$SERVER_IP "cat > /etc/nginx/sites-available/trademaker"
fi

# Enable and start
ssh root@$SERVER_IP "
    ln -sf /etc/nginx/sites-available/trademaker /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    systemctl daemon-reload
    systemctl enable trademaker
    systemctl start trademaker
"

echo ""
echo "========================================"
echo " Deploy Complete!"
echo " "
echo " Check status:"
echo "   ssh root@$SERVER_IP systemctl status trademaker"
echo "   ssh root@$SERVER_IP systemctl status nginx"
echo " "
echo " View logs:"
echo "   ssh root@$SERVER_IP journalctl -u trademaker -f"
echo ""
echo " URL: http://$SERVER_IP"
if [ -n "$DOMAIN" ]; then
    echo " URL: http://$DOMAIN"
fi
echo "========================================"
