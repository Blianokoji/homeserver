# 🚀 Self-Hosted Applications Directory & Reference Manual

This document is the **definitive catalog and operational reference** for all self-hosted services running on `homeserver`. It details access points, storage mappings on `/mnt/storage`, default credentials, and administration commands.

> **Interactive Port Tool & Protocol**: Use [`portexplain`](~/.local/bin/portexplain) to view live listening ports and the hit list in your terminal, and [`caddy-proxies`](~/.local/bin/caddy-proxies) to inspect and test all container reverse proxies and subdomains. For port allocation rules and adding new services, see [`PORTEXPLAIN_REGISTRY.md`](~/PORTEXPLAIN_REGISTRY.md).

---

## 🖥️ Server System Metadata

| Property | Value | Description |
| :--- | :--- | :--- |
| **Hostname** | `homeserver` | Resolves locally via mDNS / Tailscale MagicDNS |
| **Local IP (LAN)** | `<lan-ip>` | Home Wi-Fi / Ethernet subnet |
| **Tailscale IP (VPN)** | `<tailscale-ip>` | Encrypted mesh network IP (accessible worldwide) |
| **Tailscale Domain** | `<tailscale-domain>` | Full MagicDNS FQDN |
| **Storage Root (HDD)** | `/mnt/storage` | 1 TB persistent drive for all media, appdata, and downloads |
| **System Drive (SSD)** | `/` (120 GB SSD) | OS, kernel, Docker daemon runtime |
| **Hardware GPU** | NVIDIA GeForce GTX 1050 Ti | NVENC / NVDEC hardware transcoding & CUDA runtime |

---

## 🌐 Master Application Directory

| Application | Category | Local LAN URL | Tailscale URL | Port | Default / Setup Credentials | Compose Stack Directory |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Caddy** | 🌐 Reverse Proxy & Gateway | [https://<lan-ip>](https://<lan-ip>) | [https://<tailscale-ip>](https://<tailscale-ip>) | `80`, `443` | Managed via Tailscale Access Grants & LAN | `/mnt/storage/AppData/caddy` |
| **Glance** | 📊 Startpage & Hub | [http://<lan-ip>:8088](http://<lan-ip>:8088) | [http://<tailscale-ip>:8088](http://<tailscale-ip>:8088) | `8088` | Configured via `glance.yml` | `/mnt/storage/AppData/services` |
| **Immich** | 📸 Photos & Videos | [http://<lan-ip>:2283](http://<lan-ip>:2283) | [http://<tailscale-ip>:2283](http://<tailscale-ip>:2283) | `2283` | Initial setup on first visit | `/mnt/storage/AppData/immich` |
| **Jellyfin** | 🎬 Media Streaming | [http://<lan-ip>:8096](http://<lan-ip>:8096) | [http://<tailscale-ip>:8096](http://<tailscale-ip>:8096) | `8096` | Initial setup wizard (NVENC enabled) | `/mnt/storage/AppData/services` |
| **Jellyseerr** | 🎯 Media Requests | [http://<lan-ip>:5055](http://<lan-ip>:5055) | [http://<tailscale-ip>:5055](http://<tailscale-ip>:5055) | `5055` | Sign in with Jellyfin account | `/mnt/storage/AppData/services` |
| **Prowlarr** | 🌐 Indexer Proxy | [http://<lan-ip>:9696](http://<lan-ip>:9696) | [http://<tailscale-ip>:9696](http://<tailscale-ip>:9696) | `9696` | Setup authentication in Settings | `/mnt/storage/AppData/services` |
| **FlareSolverr** | 🛡️ Cloudflare Proxy | [http://<lan-ip>:8191](http://<lan-ip>:8191) | [http://<tailscale-ip>:8191](http://<tailscale-ip>:8191) | `8191` | REST API on port 8191 | `/mnt/storage/AppData/services` |
| **Radarr** | 🎬 Movie Automation | [http://<lan-ip>:7878](http://<lan-ip>:7878) | [http://<tailscale-ip>:7878](http://<tailscale-ip>:7878) | `7878` | Setup authentication in Settings | `/mnt/storage/AppData/services` |
| **Sonarr** | 📺 TV Automation | [http://<lan-ip>:8989](http://<lan-ip>:8989) | [http://<tailscale-ip>:8989](http://<tailscale-ip>:8989) | `8989` | Setup authentication in Settings | `/mnt/storage/AppData/services` |
| **Bazarr** | 💬 Subtitles | [http://<lan-ip>:6767](http://<lan-ip>:6767) | [http://<tailscale-ip>:6767](http://<tailscale-ip>:6767) | `6767` | Setup authentication in Settings | `/mnt/storage/AppData/services` |
| **Lidarr** | 🎵 Music Automation | [http://<lan-ip>:8686](http://<lan-ip>:8686) | [http://<tailscale-ip>:8686](http://<tailscale-ip>:8686) | `8686` | Setup authentication in Settings | `/mnt/storage/AppData/services` |
| **qBittorrent** | 📥 24/7 Downloads | [http://<lan-ip>:8085](http://<lan-ip>:8085) | [http://<tailscale-ip>:8085](http://<tailscale-ip>:8085) | `8085` | Configured during initial setup wizard | `/mnt/storage/AppData/services` |
| **Docmost** | 📚 Knowledge Base | [http://<lan-ip>:3002](http://<lan-ip>:3002) | [http://<tailscale-ip>:3002](http://<tailscale-ip>:3002) | `3002` | Create admin account on first visit | `/mnt/storage/AppData/docmost` |
| **Hoarder** | 🔖 AI Bookmark App | [http://<lan-ip>:3030](http://<lan-ip>:3030) | [http://<tailscale-ip>:3030](http://<tailscale-ip>:3030) | `3030` | Create admin account on first visit | `/mnt/storage/AppData/hoarder` |
| **Home Assistant** | 🏡 Smart Home Hub | [http://<lan-ip>:8123](http://<lan-ip>:8123) | [http://<tailscale-ip>:8123](http://<tailscale-ip>:8123) | `8123` | Initial onboarding wizard | `/mnt/storage/AppData/services` |
| **Vaultwarden** | 🔐 Password Vault | [http://<lan-ip>:8083](http://<lan-ip>:8083) | [http://<tailscale-ip>:8083](http://<tailscale-ip>:8083) | `8083` | Create master account on first visit | `/mnt/storage/AppData/services` |
| **FileBrowser** | 📁 Storage Manager | [http://<lan-ip>:8082](http://<lan-ip>:8082) | [http://<tailscale-ip>:8082](http://<tailscale-ip>:8082) | `8082` | Default: Initial setup wizard | `/mnt/storage/AppData/services` |
| **Audiobookshelf** | 🎧 Audiobooks/Podcasts | [http://<lan-ip>:13378](http://<lan-ip>:13378)| [http://<tailscale-ip>:13378](http://<tailscale-ip>:13378)| `13378`| Create root account on first visit | `/mnt/storage/AppData/services` |
| **Navidrome** | 🎵 Music Server | [http://<lan-ip>:4533](http://<lan-ip>:4533) | [http://<tailscale-ip>:4533](http://<tailscale-ip>:4533) | `4533` | Create admin account on first visit | `/mnt/storage/AppData/services` |
| **Uptime Kuma** | 📊 Service Monitor | [http://<lan-ip>:3001](http://<lan-ip>:3001) | [http://<tailscale-ip>:3001](http://<tailscale-ip>:3001) | `3001` | Create admin account on first visit | `/mnt/storage/AppData/services` |
| **AdGuard Home** | 🛡️ DNS Ad-Blocker | [http://<lan-ip>:8053](http://<lan-ip>:8053) | [http://<tailscale-ip>:8053](http://<tailscale-ip>:8053) | `8053` / `53` | Setup on port `3000` / Web: `8053` | `/mnt/storage/AppData/services` |
| **Grafana** | 📈 Metrics Dashboard | [http://<lan-ip>:3005](http://<lan-ip>:3005) | [http://<tailscale-ip>:3005](http://<tailscale-ip>:3005) | `3005` | User: `admin` \| Password: `admin` | `/mnt/storage/AppData/services` |
| **Prometheus** | 📊 Telemetry Engine | [http://<lan-ip>:9090](http://<lan-ip>:9090) | [http://<tailscale-ip>:9090](http://<tailscale-ip>:9090) | `9090` | Open Metrics Console | `/mnt/storage/AppData/services` |
| **Node Exporter** | ⚙️ Hardware Metrics | [http://<lan-ip>:9100](http://<lan-ip>:9100) | [http://<tailscale-ip>:9100](http://<tailscale-ip>:9100) | `9100` | Raw Metrics Stream (`/metrics`) | `/mnt/storage/AppData/services` |
| **CasaOS** | 🏠 Web Dashboard | [http://<lan-ip>](http://<lan-ip>) | [http://<tailscale-ip>](http://<tailscale-ip>) | `80` | Initial setup on first visit | Host service (`casaos.service`) |
| **Portainer CE** | 🐳 Docker Web UI | [https://<lan-ip>:9443](https://<lan-ip>:9443)| [https://<tailscale-ip>:9443](https://<tailscale-ip>:9443)| `9443`| Create admin account on first visit | Standalone Docker container |
| **Sunshine** | 🖥️ Remote Desktop | [https://<lan-ip>:47990](https://<lan-ip>:47990)| [https://<tailscale-ip>:47990](https://<tailscale-ip>:47990)| `47990`| Create credentials on first visit | Systemd User Service |
| **CUPS & AirPrint** | 🖨️ Print Server & Dropzone | [http://<lan-ip>:631](http://<lan-ip>:631) \| [WebPrint: 8084](http://<lan-ip>:8084) | [http://<tailscale-ip>:631](http://<tailscale-ip>:631) \| [WebPrint: 8084](http://<tailscale-ip>:8084) | `631`, `8084` | Configured via `CUPS_USER` & `CUPS_PASSWORD` | `/mnt/storage/AppData/cups` |
| **SearXNG** | 🔎 Metasearch Engine | [http://<lan-ip>:8080](http://<lan-ip>:8080) | [http://<tailscale-ip>:8080](http://<tailscale-ip>:8080) | `8080` | No auth / JSON search API enabled | `/mnt/storage/AppData/searxng` |
| **Ollama** | 🦙 Local LLM Inference | [http://<lan-ip>:11434](http://<lan-ip>:11434) | [http://<tailscale-ip>:11434](http://<tailscale-ip>:11434) | `11434` | HTTP REST API / GPU Accelerated | `/mnt/storage/AppData/ollama` |
| **IPTV Gateway** | 📺 Live TV & Streaming | [http://<lan-ip>:8484](http://<lan-ip>:8484) | [http://<tailscale-ip>:8484](http://<tailscale-ip>:8484) | `8484` | Public Web Dashboard & Tuner Endpoint | `/mnt/storage/AppData/iptv-proxy` |
| **CopyPop** | 📋 File Sharing & Clipboard | [http://<lan-ip>:18080](http://<lan-ip>:18080) | [http://<tailscale-ip>:18080](http://<tailscale-ip>:18080) | `18080` | Passkey: Configured via environment variable | Systemd User Service (`copypop.service`) |

---

## 📦 Application Profiles & Configuration Details

### 1. 📊 Glance (Homelab Startpage & Dashboard)
* **Container**: `glance`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Configuration**: [`/mnt/storage/AppData/glance/glance.yml`](file:///mnt/storage/AppData/glance/glance.yml)
* **Key Features**:
  * Unified, ultra-fast homeserver dashboard with real-time clock, search, system hardware monitors (CPU, Memory, Storage), weather, launcher bookmarks, and tech news RSS feeds.

---

### 2. 🎯 Jellyseerr (Media Discovery & Request Portal)
* **Container**: `jellyseerr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**: `/mnt/storage/AppData/jellyseerr` (config), `/mnt/storage/Downloads` (mounted to `/downloads`)
* **Key Features**:
  * Seamless Jellyfin integration: users can browse trending movies/shows, watch trailers, and request media with 1-click. Automatically sends requests to Radarr and Sonarr.
  * **Enhanced "Delete Requested" Engine**: Custom backend automation (`custom-delete-requested.js` and `apply-patches.sh`) that intercepts request deletion to automatically stop/pause active torrents in qBittorrent, purge torrent data and leftover downloaded files (`/downloads`), remove series/movies from Sonarr/Radarr, and reset media records in Jellyseerr.
  * **CLI Management**: [`jellyseerr-delete-requested`](~/.local/bin/jellyseerr-delete-requested) allows listing requests and performing comprehensive request/download/data removal from the command line.

---

### 3. 🌐 Prowlarr (Indexer & Tracker Proxy)
* **Container**: `prowlarr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**: `/mnt/storage/AppData/prowlarr`
* **Key Features**:
  * Central indexer hub that connects to public and private trackers, seamlessly synchronizing them into Radarr, Sonarr, and Lidarr without per-app configuration.

---

### 4. 🎬 Radarr (Automated Movie Manager)
* **Container**: `radarr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Config: `/mnt/storage/AppData/radarr`
  * Media Library: `/mnt/storage/Media/Movies`
  * Downloads: `/mnt/storage/Downloads`
* **Key Features**:
  * Automated movie grabber, quality upgrader, and file organizer connecting directly to qBittorrent and Jellyfin.

---

### 5. 📺 Sonarr (Automated TV Series Manager)
* **Container**: `sonarr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Config: `/mnt/storage/AppData/sonarr`
  * Media Library: `/mnt/storage/Media/TV`
  * Downloads: `/mnt/storage/Downloads`
* **Key Features**:
  * Automatically tracks TV shows, anime, missing episodes, grabs new releases via qBittorrent, and organizes them cleanly into Jellyfin libraries.

---

### 6. 💬 Bazarr (Automated Subtitle Downloader)
* **Container**: `bazarr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Config: `/mnt/storage/AppData/bazarr`
  * Media: `/mnt/storage/Media/Movies`, `/mnt/storage/Media/TV`
* **Key Features**:
  * Companion to Radarr and Sonarr that automatically scans for and downloads missing subtitles across multiple providers.

---

### 7. 🎵 Lidarr (Automated Music Discography Manager)
* **Container**: `lidarr`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Config: `/mnt/storage/AppData/lidarr`
  * Music Library: `/mnt/storage/Media/Music`
  * Downloads: `/mnt/storage/Downloads`
* **Key Features**:
  * Tracks music artist discographies, fetches albums via qBittorrent, tags metadata, and places files into Navidrome.

---

### 8. 📚 Docmost (Collaborative Wiki & Knowledge Base)
* **Containers**: `docmost`, `docmost_db`, `docmost_redis`
* **Compose File**: [`/mnt/storage/AppData/docmost/docker-compose.yml`](file:///mnt/storage/AppData/docmost/docker-compose.yml)
* **Storage Paths**:
  * Storage: `/mnt/storage/AppData/docmost/data`
  * Database: `/mnt/storage/AppData/docmost/db`
  * Redis: `/mnt/storage/AppData/docmost/redis`
* **Key Features**:
  * Modern Notion alternative for homelab documentation, personal wikis, and structured notes.

---

### 9. 🔖 Hoarder (AI Bookmark & Link Hoarder)
* **Containers**: `hoarder_web`, `hoarder_meilisearch`, `hoarder_redis`, `hoarder_chrome`
* **Compose File**: [`/mnt/storage/AppData/hoarder/docker-compose.yml`](file:///mnt/storage/AppData/hoarder/docker-compose.yml)
* **Storage Paths**:
  * Storage: `/mnt/storage/AppData/hoarder/data`
  * Meilisearch: `/mnt/storage/AppData/hoarder/meilisearch`
  * Redis: `/mnt/storage/AppData/hoarder/redis`
* **Key Features**:
  * Bookmark and link hoarder with automated web crawling, screenshot capture, full-text search, and AI tagging.

---

### 10. 🏡 Home Assistant (Smart Home Hub & Automation)
* **Container**: `homeassistant`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**: `/mnt/storage/AppData/homeassistant`
* **Key Features**:
  * Central smart home platform connecting all local smart devices, network presence, and automations.

---

### 11. 📈 Prometheus + Node Exporter + Grafana (Infrastructure Telemetry)
* **Containers**: `prometheus`, `node_exporter`, `grafana`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Prometheus TSDB: `/mnt/storage/AppData/prometheus/data`
  * Prometheus Config: `/mnt/storage/AppData/prometheus/prometheus.yml`
  * Grafana Data: `/mnt/storage/AppData/grafana`
* **Key Features**:
  * Real-time hardware telemetry (CPU load/temperature, memory saturation, disk I/O, network bandwidth, container metrics).

---

### 12. 📸 Immich (Self-Hosted Google Photos Alternative)
* **Containers**: `immich_server`, `immich_machine_learning`, `immich_postgres`, `immich_redis`
* **Compose File**: [`/mnt/storage/AppData/immich/docker-compose.yml`](file:///mnt/storage/AppData/immich/docker-compose.yml)
* **Storage Paths**:
  * Photos & Videos: `/mnt/storage/Media/Immich`
  * Database: `/mnt/storage/AppData/immich/postgres`
  * AI Model Cache: `/mnt/storage/AppData/immich/model-cache`
* **Key Features**:
  * Multi-user private accounts with AI facial recognition, object search, and timeline view.
  * **Storage Template** (`{{user.name}}/{{y}}/{{MM}}/{{filename}}`) segregates media into distinct folders per user on the physical hard drive.

---

### 13. 🎬 Jellyfin (Media & Video Streaming Server)
* **Container**: `jellyfin`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Media Library: `/mnt/storage/Media` (`/media/movies`, `/media/tv`, `/media/music`)
  * Config & Cache: `/mnt/storage/AppData/jellyfin/config`, `/mnt/storage/AppData/jellyfin/cache`
* **Hardware Acceleration**:
  * NVIDIA GTX 1050 Ti NVENC enabled via Docker runtime for on-the-fly 1080p/4K video transcoding.
* **Mobile Responsiveness & Theme UI/UX**:
  * Configured in `/mnt/storage/AppData/jellyfin/config/config/branding.xml` with ultra-responsive mobile engine built on JellySkin (`@luppodev/jellyskin`).
  * Seamless mobile login page (natural flexbox viewport centering, no keyboard cutoff, 16px inputs to prevent iOS auto-zoom, responsive user avatar grids).
  * Full mobile UI responsiveness across top app bar, drawer, horizontal swiping scrollers, detail pages, native-style bottom action sheets, and touch-target optimization.

---

### 14. 📥 qBittorrent (24/7 Remote Torrent Downloader)
* **Container**: `qbittorrent`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Download Directory: `/mnt/storage/Downloads`
  * Configuration: `/mnt/storage/AppData/qbittorrent/config`

---

### 15. 🔐 Vaultwarden (Private Password Manager)
* **Container**: `vaultwarden`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Encrypted Vault Data: `/mnt/storage/AppData/vaultwarden/data`

---

### 16. 📁 FileBrowser (Web File Manager)
* **Container**: `filebrowser`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Managed Root: `/mnt/storage` (`/srv`)
  * Database & Settings: `/mnt/storage/AppData/filebrowser`

---

### 17. 🎧 Audiobookshelf (Audiobooks & Podcasts)
* **Container**: `audiobookshelf`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Audiobooks: `/mnt/storage/Media/Audiobooks`
  * Podcasts: `/mnt/storage/Media/Podcasts`
  * Config & Metadata: `/mnt/storage/AppData/audiobookshelf`

---

### 18. 🎵 Navidrome (High-Performance Music Server)
* **Container**: `navidrome`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Music Library: `/mnt/storage/Media/Music`
  * Database & Cache: `/mnt/storage/AppData/navidrome/data`

---

### 19. 🛡️ AdGuard Home (Network-Wide DNS Ad-Blocker)
* **Container**: `adguardhome`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Config & Rules: `/mnt/storage/AppData/adguardhome/conf`, `/mnt/storage/AppData/adguardhome/work`

---

### 20. 📊 Uptime Kuma (Server Monitoring & Alerts)
* **Container**: `uptime_kuma`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Storage Paths**:
  * Database & History: `/mnt/storage/AppData/uptime-kuma/data`

---

### 21. 🔄 Watchtower (Automated Docker Image Updater)
* **Container**: `watchtower`
* **Compose File**: [`/mnt/storage/AppData/services/docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml)
* **Schedule**: Runs automatically at `4:00 AM` every day to pull latest images and restart containers cleanly.

---

### 22. 🖨️ CUPS & AirPrint (Print Server & Cloud WebDropzone)
* **Container**: `cups`
* **Compose File**: [`/mnt/storage/AppData/cups/docker-compose.yml`](file:///mnt/storage/AppData/cups/docker-compose.yml)
* **Storage Paths**:
  * Configuration: `/mnt/storage/AppData/cups/config`
  * Print Spool: `/mnt/storage/AppData/cups/spool`
  * Uploads / Temp: `/mnt/storage/AppData/cups/uploads`
* **Connected Hardware**: Epson EcoTank L3110 Series (USB `04b8:1142`)
* **Key Features**:
  * **Apple AirPrint**: Automatic mDNS/Bonjour discovery across home Wi-Fi for 1-tap printing from iPhone, iPad, and Mac.
  * **Android & Remote IPP**: Connect from anywhere over Tailscale using `http://<tailscale-ip>:631/printers/Epson_L3110` in Default Print Service / Mopria.
  * **Cloud WebDropzone (`:8084`)**: Mobile-first web app at `http://<tailscale-ip>:8084` to drop and print PDFs, photos, and documents from any browser with color/copies controls.
  * **CUPS Admin Console (`:631`)**: Full printer queue management, ink status, and raw job diagnostics.

---

### 23. 🔎 SearXNG (Privacy-Respecting Metasearch Engine)
* **Container**: `searxng`
* **Compose File**: [`/mnt/storage/AppData/searxng/docker-compose.yml`](file:///mnt/storage/AppData/searxng/docker-compose.yml)
* **Storage Paths**: `/mnt/storage/AppData/searxng`
* **Key Features**:
  * Sovereign metasearch aggregator aggregating results across Wikipedia, GitHub, Reddit, and web engines.
  * Native JSON API output enabled (`/search?q=...&format=json`) powering Antigravity Research Engine (`ag`) and agent research without bot-blocking.

---

### 24. 🦙 Ollama (Local AI & LLM Inference Server)
* **Container**: `ollama`
* **Compose File**: [`/mnt/storage/AppData/ollama/docker-compose.yml`](file:///mnt/storage/AppData/ollama/docker-compose.yml)
* **Storage Paths**: `/mnt/storage/AppData/ollama` (mapped to `/root/.ollama` for models)
* **Key Features**:
  * Hardware-accelerated LLM inference using the dedicated NVIDIA GeForce GTX 1050 Ti (4GB VRAM).
  * High-performance local API on port `11434` for entity extraction, summarization, and hypothesis evaluation in `ag`.

---

### 25. 📋 CopyPop (Cross-Device File Sharing & Clipboard Sync)
* **Service**: `systemctl --user status copypop`
* **Configuration**: [`~/Projects/copypop/.env`](~/Projects/copypop/.env)
* **Storage Paths**: Uploaded attachments drop into `~/Vault/Inbox/Attachment/` and Markdown notes in `~/Vault/Inbox/`
* **CLI Utility**: [`copypop`](~/.local/bin/copypop) (`copypop start|stop|restart|enable|disable|status|qr`)
* **Key Features**:
  * PWA and mobile-friendly local upload interface for documents, PDFs, and photos.
  * Real-time clipboard synchronization into Wayland desktop using `wl-copy`.
  * Auto-starts on boot via user systemd service.

---

### 26. 📺 IPTV Live TV Gateway & EPG Engine
* **Container**: `iptv-proxy`
* **Compose File**: [`/mnt/storage/AppData/iptv-proxy/docker-compose.yml`](file:///mnt/storage/AppData/iptv-proxy/docker-compose.yml)
* **Application Script**: [`/mnt/storage/AppData/iptv-proxy/app.py`](file:///mnt/storage/AppData/iptv-proxy/app.py)
* **Storage Paths**: `/mnt/storage/AppData/iptv-proxy/data` (persistent cache file `iptv_cache.m3u`)
* **Ports**: `8484` (Web Dashboard, M3U Tuner endpoint `/playlist.m3u`, XMLTV EPG endpoint `/epg.xml`)
* **Key Features**:
  * **Multi-Source Parallel Aggregator**: Fetches and merges 10 legal free-to-air & open-source IPTV sources concurrently (Malayalam priority, Free-TV India, India National, Free-TV Global, Global News, Sports, Movies & Cinema, Kids & Animation, Documentary & Nature, Music) into 5,500+ clean channels.
  * **Safe Atomic Cache Invariants**: Writes to `iptv_cache.m3u.tmp` before atomically replacing `iptv_cache.m3u`. Aborts and retains previous cache if upstream network blips occur, guaranteeing zero empty playlist wipes.
  * **Rich Continuous 24/7 EPG Generator**: Emits XMLTV schedules across 6 time blocks per day for yesterday, today, and tomorrow. Maps categories directly to Jellyfin XMLTV categories (`News`, `Sports`, `Movie`, `Kids`, `Documentary`, `Music`) with verified channel logos.
  * **Leading Number Bug Mitigation**: Normalizes channels starting with numeric prefixes (e.g., "24 News" -> "24 News HD") preventing Jellyfin regex from stripping channel names.
  * **User-Agent Spoofing Stream Proxy**: On-demand proxying at `/stream?url=...` with desktop browser User-Agent headers to bypass 403 Forbidden geoblocks.
  * **Jellyfin Integration**: Direct integration via M3U Tuner (`http://iptv-proxy:8484/playlist.m3u`) and XMLTV Provider (`http://iptv-proxy:8484/epg.xml`).

---

## 🛠️ Docker Stack Operations Playbook

### 1. Managing the Master Services Stack
```bash
# Navigate to stack directory
cd /mnt/storage/AppData/services

# View running status of all services
docker compose ps

# Restart a specific service (e.g. glance)
docker compose restart glance

# View live logs of a service
docker compose logs -f jellyseerr

# Recreate/update all containers after editing docker-compose.yml
docker compose up -d --remove-orphans
```

### 2. Managing Docmost & Hoarder Stacks
```bash
# Docmost stack
cd /mnt/storage/AppData/docmost && docker compose ps

# Hoarder stack
cd /mnt/storage/AppData/hoarder && docker compose ps

# CUPS Print Server stack
cd /mnt/storage/AppData/cups && docker compose ps
docker exec cups lpstat -t
```

### 3. Complete Data Backup Command
```bash
sudo tar -czvf /mnt/storage/Backups/appdata_backup_$(date +%Y%m%d_%H%M%S).tar.gz /mnt/storage/AppData
```
