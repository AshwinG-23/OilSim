#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/simPro
VENV_DIR="$APP_DIR/.venv"
SERVICE_PATH=/etc/systemd/system/simpro.service
NGINX_SITE=/etc/nginx/sites-available/simpro
NGINX_ENABLED=/etc/nginx/sites-enabled/simpro

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y python3 python3-venv python3-pip nginx

mkdir -p "$APP_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

cat > "$SERVICE_PATH" <<'EOF'
[Unit]
Description=simPro Gunicorn service
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/opt/simPro
Environment=PATH=/opt/simPro/.venv/bin
ExecStart=/opt/simPro/.venv/bin/gunicorn web.app:app --timeout 180 --workers 2 --bind 127.0.0.1:8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > "$NGINX_SITE" <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf "$NGINX_SITE" "$NGINX_ENABLED"

systemctl daemon-reload
systemctl enable simpro
systemctl restart simpro
nginx -t
systemctl restart nginx
