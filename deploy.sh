#!/bin/bash
# TradeMaster Deploy for Tencent Cloud (106.53.100.252)
# Run this on your Ubuntu server: bash /tmp/deploy_trademaster.sh

set -e
IP=106.53.100.252

echo '========================================'
echo ' TradeMaster Deploy'
echo ' Server: '
echo '========================================'

echo '[1/7] Installing system deps...'
apt update && apt install -y python3 python3-pip python3-venv nginx git

echo '[2/7] Creating directories...'
mkdir -p /var/www/trademaker /var/log/trademaker

echo '[3/7] Cloning repo...'
cd /var/www/trademaker
if [ -d .git ]; then
    git pull origin main
else
    rm -rf ./* .[^.]*
    git clone https://github.com/Jack-lei-prog/trademaker.git .
fi

echo '[4/7] Creating .env file...'
cat > .env << 'ENVEOF'
FLASK_DEBUG=0
SECRET_KEY=c6d144cf4f485667c56af6fff881fa4e5bce109e038d0f7ddabacc7e2a1d51d2
CORS_ORIGINS=http://106.53.100.252,http://localhost:5000,http://127.0.0.1:5000

LLM_API_KEY=sk-g1RmuqgbbGyO8TIPocy3vKYDApZSegAAAgxNeKVzGhtrdl0A
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=kimi-k2.7-code

LLM_BACKUP1_URL=https://api.deepseek.com/v1/chat/completions
LLM_BACKUP1_MODEL=deepseek-chat

KIMI_API_KEY=sk-g1RmuqgbbGyO8TIPocy3vKYDApZSegAAAgxNeKVzGhtrdl0A
KIMI_MODEL=kimi-k2.7-code

SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_EMAIL=your_email@qq.com
SMTP_PASSWORD=your_authorization_code
SENDER_NAME=TradeMaster

TRUSTED_PROXIES=127.0.0.1,::1
ENVEOF
echo '  .env created'

echo '[5/7] Setting up Python venv...'
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

echo '[6/7] Configuring systemd...'
cp trademaker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable trademaker
systemctl start trademaker
sleep 2
systemctl status trademaker --no-pager

echo '[7/7] Configuring nginx...'
sed "s/YOUR_DOMAIN_OR_IP//" trademaker.nginx.conf > /etc/nginx/sites-available/trademaker
ln -sf /etc/nginx/sites-available/trademaker /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

chown -R www-data:www-data /var/www/trademaker /var/log/trademaker
systemctl restart trademaker
sleep 2

echo ''
echo '========================================'
echo ' Deploy Complete!'
echo ''
echo ' Visit: http://'
echo ''
echo ' Check: systemctl status trademaker'
echo ' Logs:  journalctl -u trademaker -f'
echo '========================================'
