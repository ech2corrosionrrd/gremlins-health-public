#!/usr/bin/env bash
# ==============================================================================
#  Gremlins Health - server bootstrap (Ubuntu 24.04 / 22.04)
#
#  Prepares the host only. It does NOT deploy the app and does NOT write any
#  secrets - see README_DEPLOY.md for the deploy steps.
# ==============================================================================
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "This script must run as root." >&2
    exit 1
fi

APP_USER="gremlins"
APP_DIR="/var/www/gremlins-health"

log() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

log "[1/6] Updating system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

log "[2/6] Installing base packages"
apt-get install -y --no-install-recommends \
    curl git ufw nginx certbot python3-certbot-nginx \
    python3-venv python3-pip ca-certificates

log "[3/6] Installing Docker (optional path)"
if ! command -v docker >/dev/null 2>&1; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "Docker already installed; skipping."
fi

log "[4/6] Configuring firewall"
# Allow SSH before enabling, or the session is cut.
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# 5432 (Postgres), 6379 (Redis) and 8000 (uvicorn) stay closed: they are
# reachable only over loopback or the Docker network.
ufw --force enable
ufw status verbose

log "[5/6] Creating service account and app directory"
if ! id -u "$APP_USER" >/dev/null 2>&1; then
    useradd --system --create-home --home-dir "$APP_DIR" \
        --shell /usr/sbin/nologin "$APP_USER"
else
    echo "User $APP_USER already exists; skipping."
fi
mkdir -p "$APP_DIR" /var/www/certbot
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

log "[6/6] Done"
cat <<EOF

Host is ready. Remaining steps (see deploy/README_DEPLOY.md):

  1. Clone the repository into $APP_DIR
  2. cp .env.example .env  and fill in every value
       SECRET_KEY: python3 -c "import secrets; print(secrets.token_urlsafe(48))"
  3. chmod 600 .env && chown $APP_USER:$APP_USER .env
  4. Run database migrations:  alembic upgrade head
  5. Install the systemd units from deploy/ and enable them
  6. certbot --nginx -d your-domain.example

Nothing above writes a secret to disk - that is deliberate.
EOF
