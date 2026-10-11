# 🎯 Homeserver Self-Hosted Services Hit List & Port Audit Protocol

This document is the **definitive operational Hit List and Port Management Protocol** for all self-hosted software running on `homeserver`. It works in conjunction with the `portexplain` CLI utility to guarantee complete visibility, avoid port collisions, and enforce automated registry synchronization across all AI agents and system administrators.

---

## 🚀 Live Port Inspection CLI: `portexplain`

The system is equipped with the custom `portexplain` CLI tool located at `~/.local/bin/portexplain`.

### Quick Usage Commands
```bash
# 1. Full system report: Master Hit List + Active Listening Network Sockets + Health Summary
portexplain

# 2. Targeted deep-dive into a specific port or service name
portexplain 8096
portexplain immich

# 3. View ONLY the Master Self-Hosted Hit List table
portexplain --hitlist

# 4. View ONLY the real-time active listening network sockets
portexplain --listening

# 5. Run health & uncataloged socket audit check
portexplain --audit

# 6. Export complete live server network state as JSON
portexplain --json

# 7. Interactive registration wizard to add a new self-hosted app
portexplain --add
```

---

## 📋 Master Self-Hosted Services Hit List

| Application | Category | Port(s) | Type / Stack Directory | Local LAN URL | Tailscale URL | Persistent Storage Path | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🌐 Caddy Reverse Proxy** | Gateway & TLS Proxy | `80`, `443` | Docker (`/mnt/storage/AppData/caddy`) | `https://<lan-ip>` | `https://<tailscale-ip>` | `/mnt/storage/AppData/caddy` | Production reverse proxy, automated local TLS, Tailscale application gateway |
| **📊 Glance** | Startpage & Hub | `8088` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8088` | `http://<tailscale-ip>:8088` | `/mnt/storage/AppData/glance` | Unified homelab dashboard with hardware telemetry, weather, and RSS feeds |
| **📸 Immich** | Photos & Videos | `2283` | Docker (`/mnt/storage/AppData/immich`) | `http://<lan-ip>:2283` | `http://<tailscale-ip>:2283` | `/mnt/storage/Media/Immich`, `/mnt/storage/AppData/immich` | Self-hosted Google Photos alternative with AI face/object recognition and user isolation |
| **🎬 Jellyfin** | Media Streaming | `8096` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8096` | `http://<tailscale-ip>:8096` | `/mnt/storage/Media`, `/mnt/storage/AppData/jellyfin` | Hardware-accelerated (NVENC GTX 1050 Ti) 4K/1080p media streaming server |
| **🎯 Jellyseerr** | Media Requests | `5055` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:5055` | `http://<tailscale-ip>:5055` | `/mnt/storage/AppData/jellyseerr` | Media discovery and 1-click request portal integrating with Jellyfin, Radarr, Sonarr |
| **🌐 Prowlarr** | Indexer Proxy | `9696` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:9696` | `http://<tailscale-ip>:9696` | `/mnt/storage/AppData/prowlarr` | Central indexer & tracker management proxy synchronizing with *arr apps |
| **🛡️ FlareSolverr** | Cloudflare Proxy | `8191` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8191` | `http://<tailscale-ip>:8191` | Daemon runtime | Proxy server to bypass Cloudflare protection for Prowlarr indexers |
| **🎬 Radarr** | Movie Automation | `7878` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:7878` | `http://<tailscale-ip>:7878` | `/mnt/storage/AppData/radarr`, `/mnt/storage/Media/Movies` | Automated movie grabber, quality upgrader, and file organizer |
| **📺 Sonarr** | TV Automation | `8989` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8989` | `http://<tailscale-ip>:8989` | `/mnt/storage/AppData/sonarr`, `/mnt/storage/Media/TV` | Automated TV show and anime release tracking, downloading, and sorting |
| **💬 Bazarr** | Subtitles | `6767` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:6767` | `http://<tailscale-ip>:6767` | `/mnt/storage/AppData/bazarr` | Automated multi-provider subtitle downloader companion for Radarr and Sonarr |
| **🎵 Lidarr** | Music Automation | `8686` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8686` | `http://<tailscale-ip>:8686` | `/mnt/storage/AppData/lidarr`, `/mnt/storage/Media/Music` | Automated music discography tracker, metadata tagger, and grabber |
| **📥 qBittorrent** | 24/7 Downloads | `8085`, `6881` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8085` | `http://<tailscale-ip>:8085` | `/mnt/storage/AppData/qbittorrent`, `/mnt/storage/Downloads` | Headless 24/7 BitTorrent download client with Web UI (8085) and peer port (6881) |
| **📚 Docmost** | Knowledge Base | `3002` | Docker (`/mnt/storage/AppData/docmost`) | `http://<lan-ip>:3002` | `http://<tailscale-ip>:3002` | `/mnt/storage/AppData/docmost` | Modern Notion alternative for collaborative documentation and personal wikis |
| **🔖 Hoarder** | AI Bookmark App | `3030` | Docker (`/mnt/storage/AppData/hoarder`) | `http://<lan-ip>:3030` | `http://<tailscale-ip>:3030` | `/mnt/storage/AppData/hoarder` | AI-powered bookmarking and web clipper with automatic text extraction & search |
| **🏡 Home Assistant** | Smart Home Hub | `8123` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8123` | `http://<tailscale-ip>:8123` | `/mnt/storage/AppData/homeassistant` | Central smart home platform connecting all local smart devices and automations |
| **🔐 Vaultwarden** | Password Vault | `8083` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8083` | `http://<tailscale-ip>:8083` | `/mnt/storage/AppData/vaultwarden` | Lightweight Bitwarden-compatible private password manager and secure vault |
| **📁 FileBrowser** | Storage Manager | `8082` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8082` | `http://<tailscale-ip>:8082` | `/mnt/storage/AppData/filebrowser`, `/mnt/storage` | Web-based file manager providing browser upload/download for `/mnt/storage` |
| **🎧 Audiobookshelf** | Audiobooks/Podcasts | `13378` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:13378` | `http://<tailscale-ip>:13378` | `/mnt/storage/Media/Audiobooks`, `/mnt/storage/AppData/audiobookshelf` | Self-hosted audiobook and podcast streaming server with progress syncing |
| **🎵 Navidrome** | Music Server | `4533` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:4533` | `http://<tailscale-ip>:4533` | `/mnt/storage/Media/Music`, `/mnt/storage/AppData/navidrome` | Subsonic-compatible high-performance streaming server for music libraries |
| **📊 Uptime Kuma** | Service Monitor | `3001` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:3001` | `http://<tailscale-ip>:3001` | `/mnt/storage/AppData/uptime-kuma` | Real-time service uptime, HTTP/ping health monitoring, and alerting dashboard |
| **🛡️ AdGuard Home** | DNS Ad-Blocker | `8053`, `53`, `3000` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:8053` | `http://<tailscale-ip>:8053` | `/mnt/storage/AppData/adguardhome` | Network-wide DNS server with ad-blocking, privacy protection, and encrypted DNS |
| **📈 Grafana** | Metrics Dashboard | `3005` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:3005` | `http://<tailscale-ip>:3005` | `/mnt/storage/AppData/grafana` | Analytics and visual dashboard suite connecting to Prometheus telemetry |
| **📊 Prometheus** | Telemetry Engine | `9090` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:9090` | `http://<tailscale-ip>:9090` | `/mnt/storage/AppData/prometheus` | Time-series telemetry database scraping metrics from Node Exporter and Docker |
| **⚙️ Node Exporter** | Hardware Metrics | `9100` | Docker (`/mnt/storage/AppData/services`) | `http://<lan-ip>:9100` | `http://<tailscale-ip>:9100` | Host metric probe | Hardware and OS kernel metrics exporter feeding Prometheus |
| **🏠 CasaOS** | Web Dashboard | `80` | Systemd Service (`casaos.service`) | `http://<lan-ip>` | `http://<tailscale-ip>` | `/etc/casaos` | Homelab web dashboard, app store, and drive management interface |
| **🐳 Portainer CE** | Docker Web UI | `9443` | Standalone Docker | `https://<lan-ip>:9443` | `https://<tailscale-ip>:9443` | `/mnt/storage/AppData/portainer` | Centralized web UI for Docker containers, images, volumes, and networks |
| **🖥️ Sunshine** | Remote Desktop | `47990`, `47984-48010` | Systemd User Service | `https://<lan-ip>:47990` | `https://<tailscale-ip>:47990` | `~/.config/sunshine` | Low-latency NVIDIA NVENC game & desktop streaming server for Moonlight |
| **🖨️ CUPS & AirPrint** | Print Server & Mobile Printing | `631`, `8084` | Docker (`/mnt/storage/AppData/cups`) | `http://<lan-ip>:631` \| `WebPrint: 8084` | `http://<tailscale-ip>:631` \| `WebPrint: 8084` | `/mnt/storage/AppData/cups` | CUPS IPP/AirPrint print server with Epson L3110 ESC/P-R driver & WebDropzone (8084) |
| **🔎 SearXNG** | Metasearch Engine | `8080` | Docker (`/mnt/storage/AppData/searxng`) | `http://<lan-ip>:8080` | `http://<tailscale-ip>:8080` | `/mnt/storage/AppData/searxng` | Privacy-respecting sovereign metasearch engine aggregating queries for AI agents and users |
| **🦙 Ollama** | Local LLM Inference | `11434` | Docker (`/mnt/storage/AppData/ollama`) | `http://<lan-ip>:11434` | `http://<tailscale-ip>:11434` | `/mnt/storage/AppData/ollama` | Local LLM inference engine with NVIDIA GTX 1050 Ti GPU acceleration for AI research and agents |
| **📺 IPTV Gateway** | Live TV & Streaming | `8484` | Docker (`/mnt/storage/AppData/iptv-proxy`) | `http://<lan-ip>:8484` | `http://<tailscale-ip>:8484` | `/mnt/storage/AppData/iptv-proxy` | Ultra-lightweight IPTV proxy, playlist optimizer, and Live TV gateway for Jellyfin with channel logos |
| **📋 CopyPop** | File Sharing & Clipboard | `18080` | Systemd User Service (`copypop.service`) | `http://<lan-ip>:18080` | `http://<tailscale-ip>:18080` | `~/.config/copypop/.env` | Cross-device file & image sharing and clipboard syncing service saving directly to Obsidian Inbox |
| **🔄 Watchtower** | Auto-Updater | Internal | Docker (`/mnt/storage/AppData/services`) | N/A | N/A | Daemon runtime | Automated container updater running daily at 4:00 AM |


---

## 🛡️ Protocol for AI Agents & Admins (Adding New Software & Auditing)

> [!IMPORTANT]
> Whenever adding, deploying, migrating, or auditing ANY software, service, container, or port on this homeserver, all AI agents (Antigravity and others) and human operators **MUST STRICTLY FOLLOW THIS 4-STEP PROTOCOL**.

### Step 1: Pre-Allocation Port Collision Check
1. Run `portexplain <desired_port>` or inspect the table above to verify that the proposed port is completely free.
2. Never reuse or bind conflicting ports.

### Step 2: Storage Layout & Reliability Invariants
1. Create the persistent configuration directory under `/mnt/storage/AppData/<service_id>`.
2. Ensure Docker Compose specifies `restart: always` (or `restart: unless-stopped`).
3. Ensure large media files map to `/mnt/storage/Media/<category>` and downloads map to `/mnt/storage/Downloads`.

### Step 3: Registering the Software in `services.json`
Add the new service configuration to `~/.config/portexplain/services.json` under `selfhosted_services`:
```json
{
  "id": "new_service_id",
  "name": "Service Display Name",
  "icon": "📦",
  "category": "Category Name",
  "ports": [8099],
  "web_port": 8099,
  "protocol": "http",
  "container_names": ["new_container_name"],
  "service_type": "docker_compose",
  "compose_dir": "/mnt/storage/AppData/new_service",
  "config_path": "/mnt/storage/AppData/new_service/config",
  "description": "Brief description of the service role and features",
  "default_creds": "Initial setup wizard / credentials"
}
```
*Tip: You can also run `portexplain --add` for an interactive wizard.*

### Step 4: Synchronize Documentation Files
Immediately append the new service entry to:
1. `PORTEXPLAIN_REGISTRY.md` (this document)
2. `SELF_HOSTED_APPS.md` (master application directory & profile section)
3. `HOMESERVER_GUIDE.md` (quick reference table & upgrade log)

---

## 🔍 Continuous Audit & Self-Healing Policy

* When auditing the server or when `portexplain --audit` detects an **Unregistered Active Socket**, investigate the process or container immediately:
  * If it is a newly deployed self-hosted application, execute **Step 3 & Step 4** above to add it to the catalog.
  * If it is an internal helper database or cache (e.g. Postgres, Redis, Meilisearch), add it to `known_system_ports` in `services.json`.
  * If it is an unintended or abandoned socket, shut down and remove the orphaned container/process.
