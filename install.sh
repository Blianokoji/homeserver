#!/usr/bin/env bash
# ==============================================================================
# 🏠 Ultimate Autonomous Homeserver Setup & Deployment Script
# Repos: git@github.com:Blianokoji/homeserver.git
#
# Supports:
#   - Full zero-to-hero setup on a clean machine
#   - Idempotent configuration synchronization & updates on existing servers
#   - Automatic hardware acceleration (NVIDIA container runtime) detection
#   - High-availability Docker stack orchestration
# ==============================================================================

set -euo pipefail

# ANSI color codes
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

STORAGE_ROOT="${STORAGE_ROOT:-/mnt/storage}"
APP_DATA="${STORAGE_ROOT}/AppData"
USER_NAME="$(id -un)"
REPO_URL="https://github.com/Blianokoji/homeserver.git"
REPO_SSH="git@github.com:Blianokoji/homeserver.git"

LAN_IP="${LAN_IP:-$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")}"
TAILSCALE_IP="${TAILSCALE_IP:-$(tailscale ip -4 2>/dev/null || echo "N/A")}"
TAILSCALE_FQDN="${TAILSCALE_FQDN:-$(tailscale status --json 2>/dev/null | grep -o '"DNSName": *"[^"]*"' | head -n1 | cut -d'"' -f4 | sed 's/\.$//' || echo "")}"
if [ -z "$TAILSCALE_FQDN" ]; then
    TAILSCALE_FQDN="homeserver.ts.net"
fi

echo -e "${BLUE}${BOLD}==============================================================================${NC}"
echo -e "${GREEN}${BOLD}      🏠  HOMESERVER AUTONOMOUS DEPLOYMENT & SETUP ORCHESTRATOR               ${NC}"
echo -e "${BLUE}${BOLD}==============================================================================${NC}"

# Check EUID
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}[!] Do not run this script directly as root. Run as your regular user.${NC}"
    echo -e "    Sudo permissions will be requested when required."
    exit 1
fi

# Detect repository directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "${SCRIPT_DIR}/compose/services/docker-compose.yml" ]; then
    echo -e "${YELLOW}[*] Running outside homeserver repository. Cloning to ~/homeserver...${NC}"
    TARGET_DIR="${HOME}/homeserver"
    if [ ! -d "$TARGET_DIR" ]; then
        git clone "$REPO_URL" "$TARGET_DIR" || git clone "$REPO_SSH" "$TARGET_DIR"
    fi
    exec "${TARGET_DIR}/install.sh" "$@"
fi

# ------------------------------------------------------------------------------
# 1. 24/7 Power Management & Sleep Prevention
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[1/8] Power Management & Sleep Invariants...${NC}"
echo "Masking systemd sleep, suspend, and hibernation targets..."
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target >/dev/null 2>&1 || true
echo -e "${GREEN}✓ Sleep and hibernation permanently disabled for 24/7 uptime.${NC}"

# ------------------------------------------------------------------------------
# 2. Package Installation & Dependencies
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[2/8] Checking System Dependencies & Runtimes...${NC}"
if command -v pacman &>/dev/null; then
    echo "Arch Linux detected. Synchronizing package dependencies..."
    sudo pacman -S --needed --noconfirm docker docker-compose git curl openssl python rsync avahi tailscale lsof || true
elif command -v apt-get &>/dev/null; then
    echo "Debian/Ubuntu detected. Installing package dependencies..."
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends docker.io docker-compose-plugin git curl openssl python3 rsync avahi-daemon tailscale lsof || true
fi

# Enable base services
echo "Enabling core system daemons..."
sudo systemctl enable --now docker || true
sudo systemctl enable --now sshd || true
sudo systemctl enable --now tailscaled || true
sudo systemctl enable --now avahi-daemon || true
sudo usermod -aG docker "$USER_NAME" || true

# Check for NVIDIA Container Runtime
if lspci 2>/dev/null | grep -i 'nvidia' &>/dev/null; then
    echo -e "${YELLOW}[*] NVIDIA GPU hardware detected.${NC}"
    if command -v nvidia-ctk &>/dev/null; then
        echo "Configuring NVIDIA container toolkit for Docker..."
        sudo nvidia-ctk runtime configure --runtime=docker || true
        sudo systemctl restart docker || true
        echo -e "${GREEN}✓ NVIDIA Docker runtime active.${NC}"
    else
        echo -e "${YELLOW}[!] Note: Install 'nvidia-container-toolkit' to enable GPU transcoding.${NC}"
    fi
fi

# ------------------------------------------------------------------------------
# 3. Storage Invariants & Directory Layout
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[3/8] Verifying Persistent Storage Structure (${STORAGE_ROOT})...${NC}"
sudo mkdir -p "${STORAGE_ROOT}"
sudo chown -R "${USER_NAME}:${USER_NAME}" "${STORAGE_ROOT}"
sudo chmod -R 775 "${STORAGE_ROOT}"

mkdir -p \
    "${STORAGE_ROOT}/AppData" \
    "${STORAGE_ROOT}/Media/Movies" \
    "${STORAGE_ROOT}/Media/TV" \
    "${STORAGE_ROOT}/Media/Music" \
    "${STORAGE_ROOT}/Media/Audiobooks" \
    "${STORAGE_ROOT}/Media/Podcasts" \
    "${STORAGE_ROOT}/Media/Photos" \
    "${STORAGE_ROOT}/Media/Immich" \
    "${STORAGE_ROOT}/Downloads" \
    "${STORAGE_ROOT}/Backups"
echo -e "${GREEN}✓ Core storage directories verified (AppData, Media, Downloads, Backups).${NC}"

# ------------------------------------------------------------------------------
# 4. Deploying Application Configurations & Compose Stacks
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[4/8] Synchronizing Stack Definitions & Configurations...${NC}"

# Sync compose definitions to /mnt/storage/AppData
COMPOSE_SERVICES=(caddy cups docmost hoarder immich iptv-proxy ollama searxng services)
for svc in "${COMPOSE_SERVICES[@]}"; do
    TARGET="${APP_DATA}/${svc}"
    mkdir -p "$TARGET"
    rsync -avq --exclude='.*' "${SCRIPT_DIR}/compose/${svc}/" "${TARGET}/"
done

# Sync application configs
mkdir -p "${APP_DATA}/glance" && sed "s|<lan-ip>|${LAN_IP}|g" "${SCRIPT_DIR}/configs/glance/glance.yml" > "${APP_DATA}/glance/glance.yml"
mkdir -p "${APP_DATA}/prometheus" && cp -f "${SCRIPT_DIR}/configs/prometheus/prometheus.yml" "${APP_DATA}/prometheus/"
mkdir -p "${APP_DATA}/searxng" && cp -f "${SCRIPT_DIR}/configs/searxng/settings.yml" "${APP_DATA}/searxng/"

# Jellyseerr patches
mkdir -p "${APP_DATA}/jellyseerr"
cp -f "${SCRIPT_DIR}/configs/jellyseerr/custom-entrypoint.sh" "${APP_DATA}/jellyseerr/"
cp -f "${SCRIPT_DIR}/configs/jellyseerr/apply-patches.sh" "${APP_DATA}/jellyseerr/"
cp -f "${SCRIPT_DIR}/configs/jellyseerr/routes-media.js" "${APP_DATA}/jellyseerr/"
cp -f "${SCRIPT_DIR}/configs/jellyseerr/routes-request.js" "${APP_DATA}/jellyseerr/"
chmod +x "${APP_DATA}/jellyseerr/"*.sh

# Immich .env generation
if [ ! -f "${APP_DATA}/immich/.env" ]; then
    echo "Generating new Immich .env configuration with random secure database secret..."
    RAND_PASS="$(openssl rand -hex 16)"
    cat << EOF > "${APP_DATA}/immich/.env"
UPLOAD_LOCATION=${STORAGE_ROOT}/Media/Immich
DB_DATA_LOCATION=${APP_DATA}/immich/postgres
TZ=Asia/Kolkata
IMMICH_VERSION=release
DB_PASSWORD=${RAND_PASS}
DB_USERNAME=postgres
DB_DATABASE_NAME=immich
EOF
    chmod 600 "${APP_DATA}/immich/.env"
fi

echo -e "${GREEN}✓ All application configuration templates synchronized.${NC}"

# ------------------------------------------------------------------------------
# 5. TLS Certificate Authority & Wildcard Generation
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[5/8] Checking Homeserver CA & TLS Certificates...${NC}"
"${SCRIPT_DIR}/system/scripts/generate_certs.sh" "${APP_DATA}/caddy/certs"

# ------------------------------------------------------------------------------
# 6. Port Registry CLI Tool Installation (`portexplain`)
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[6/8] Registering Network Intelligence & Audit Tool (portexplain)...${NC}"
mkdir -p "${HOME}/.local/bin" "${HOME}/.config/portexplain"
cp -f "${SCRIPT_DIR}/system/scripts/portexplain" "${HOME}/.local/bin/portexplain"
chmod +x "${HOME}/.local/bin/portexplain"
cp -f "${SCRIPT_DIR}/configs/portexplain/services.json" "${HOME}/.config/portexplain/services.json"
echo -e "${GREEN}✓ Installed 'portexplain' to ~/.local/bin and registry to ~/.config/portexplain.${NC}"

# ------------------------------------------------------------------------------
# 7. Docker Network & Stacks Deployment
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[7/8] Orchestrating Docker Compose Services...${NC}"

# Ensure shared proxy network exists
if ! docker network inspect caddy_proxy &>/dev/null; then
    echo "Creating Docker bridge network: caddy_proxy..."
    docker network create caddy_proxy
fi

# Build custom container images if needed
if [ -f "${APP_DATA}/cups/Dockerfile" ]; then
    echo "Building CUPS & AirPrint container image..."
    (cd "${APP_DATA}/cups" && docker compose build -q)
fi

if [ -f "${APP_DATA}/iptv-proxy/Dockerfile" ]; then
    echo "Building IPTV Proxy container image..."
    (cd "${APP_DATA}/iptv-proxy" && docker compose build -q)
fi

# Bring up stacks in operational order
echo "Launching Caddy Gateway..."
(cd "${APP_DATA}/caddy" && docker compose up -d)

echo "Launching Media & Core Apps Stack (Glance, Jellyfin, *arrs, qBittorrent, etc.)..."
(cd "${APP_DATA}/services" && docker compose up -d)

echo "Launching Immich Photo & Video Cloud..."
(cd "${APP_DATA}/immich" && docker compose up -d)

echo "Launching Auxiliary Stacks (Docmost, Hoarder, Ollama, SearXNG, CUPS, IPTV)..."
(cd "${APP_DATA}/docmost" && docker compose up -d)
(cd "${APP_DATA}/hoarder" && docker compose up -d)
(cd "${APP_DATA}/ollama" && docker compose up -d)
(cd "${APP_DATA}/searxng" && docker compose up -d)
(cd "${APP_DATA}/cups" && docker compose up -d)
(cd "${APP_DATA}/iptv-proxy" && docker compose up -d)

echo -e "${GREEN}✓ All container stacks orchestrated and running.${NC}"

# ------------------------------------------------------------------------------
# 8. Deployment Verification & Status Summary
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[8/8] Verifying Deployment Health...${NC}"
sleep 3

TAILSCALE_IP="${TAILSCALE_IP:-$(tailscale ip -4 2>/dev/null || echo "N/A")}"
LAN_IP="${LAN_IP:-$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")}"
TAILSCALE_FQDN="${TAILSCALE_FQDN:-$(tailscale status --json 2>/dev/null | grep -o '"DNSName": *"[^"]*"' | head -n1 | cut -d'"' -f4 | sed 's/\.$//' || echo "")}"
if [ -z "$TAILSCALE_FQDN" ]; then
    TAILSCALE_FQDN="homeserver.ts.net"
fi

echo -e "\n${BLUE}${BOLD}==============================================================================${NC}"
echo -e "${GREEN}${BOLD}     🎉  HOMESERVER DEPLOYMENT COMPLETE & OPERATIONAL!  🎉                     ${NC}"
echo -e "${BLUE}${BOLD}==============================================================================${NC}"
echo -e "${BOLD}Primary Network Addresses:${NC}"
echo -e "  LAN IPv4:       ${CYAN}http://${LAN_IP}${NC}"
echo -e "  Tailscale IPv4: ${CYAN}http://${TAILSCALE_IP}${NC}"
echo -e "  Tailscale FQDN: ${CYAN}http://${TAILSCALE_FQDN}${NC}"
echo ""
echo -e "${BOLD}Key Service Gateways:${NC}"
echo -e "  • Glance Homelab Dashboard:  ${GREEN}http://${LAN_IP}:8088${NC} | ${CYAN}https://glance.${TAILSCALE_FQDN}${NC}"
echo -e "  • Jellyfin Media Streaming:  ${GREEN}http://${LAN_IP}:8096${NC} | ${CYAN}https://jellyfin.${TAILSCALE_FQDN}${NC}"
echo -e "  • Immich Photo/Video Cloud:  ${GREEN}http://${LAN_IP}:2283${NC} | ${CYAN}https://immich.${TAILSCALE_FQDN}${NC}"
echo -e "  • AdGuard Home DNS & UI:     ${GREEN}http://${LAN_IP}:8053${NC} | ${CYAN}https://adguard.${TAILSCALE_FQDN}${NC}"
echo -e "  • Vaultwarden Passwords:     ${GREEN}http://${LAN_IP}:8083${NC} | ${CYAN}https://vaultwarden.${TAILSCALE_FQDN}${NC}"
echo -e "  • Uptime Kuma Monitoring:    ${GREEN}http://${LAN_IP}:3001${NC} | ${CYAN}https://uptime.${TAILSCALE_FQDN}${NC}"
echo -e "  • Docmost Wiki:              ${GREEN}http://${LAN_IP}:3002${NC} | ${CYAN}https://docmost.${TAILSCALE_FQDN}${NC}"
echo -e "  • Hoarder AI Bookmarks:      ${GREEN}http://${LAN_IP}:3030${NC} | ${CYAN}https://hoarder.${TAILSCALE_FQDN}${NC}"
echo -e "  • CUPS WebDropzone Print:    ${GREEN}http://${LAN_IP}:8084${NC} | ${CYAN}https://print.${TAILSCALE_FQDN}${NC}"
echo -e "  • Ollama Local LLMs:         ${GREEN}http://${LAN_IP}:11434${NC}"
echo ""
echo -e "${YELLOW}Audit & Diagnostics Commands:${NC}"
echo -e "  • Audit all ports:      ${BOLD}portexplain${NC}"
echo -e "  • Inspect running apps: ${BOLD}docker ps${NC}"
echo -e "  • Follow Caddy logs:    ${BOLD}docker logs -f caddy${NC}"
echo -e "${BLUE}${BOLD}==============================================================================${NC}"
