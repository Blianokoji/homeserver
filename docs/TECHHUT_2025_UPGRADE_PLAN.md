# 🚀 TechHut 2025 Homelab Masterplan & Service Integration Blueprint

## 📋 Executive Summary

This masterplan evaluates the **TechHut 2025 "Must-Have Homelab Services"** catalog against the existing headless `homeserver` architecture. It identifies high-value enhancements, specifies non-conflicting port and storage mappings under `/mnt/storage`, and establishes a phased execution plan to upgrade the homeserver into an automated, self-contained powerhouse.

---

## 🔍 Service Compatibility & Gap Analysis

| TechHut 2025 Service | Category | Server Status | Integration Verdict & Enhancement Value |
| :--- | :--- | :--- | :--- |
| **Glance** | 📊 Dashboard | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 8088)**: Ultra-fast YAML-configured startpage with system stats, app bookmarks, RSS feeds, and weather. |
| **Homarr / Organizr**| 📊 Dashboard | 🔄 *Alternative*| Glance selected for lower resource footprint (<20MB RAM) and clean YAML maintenance. |
| **Jellyfin** | 🎬 Media Server | ✅ **Active (8096)** | NVIDIA GTX 1050 Ti NVENC hardware acceleration already configured. |
| **Plex / Tautulli** | 🎬 Media / Stats | 🔄 *Alternative* | Jellyfin covers media streaming without proprietary subscriptions; Jellyseerr provides unified stats and requests. |
| **Jellyseerr / Overseerr**| 🎯 Media Requests | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 5055)**: Unified discovery & 1-click media request portal for Jellyfin with automatic *arr handoff. |
| **Radarr** | 🎬 Movie Automation | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 7878)**: Automated movie search, quality upgrading, downloading via qBittorrent, and hardlinking to `/mnt/storage/Media/Movies`. |
| **Sonarr** | 📺 TV Show Automation| ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 8989)**: Automated episode tracking, anime management, renaming, and organization into `/mnt/storage/Media/TV`. |
| **Prowlarr** | 🌐 Indexer Proxy | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 9696)**: Centralized torrent tracker and Usenet indexer manager syncing directly with Sonarr, Radarr, and Lidarr. |
| **Bazarr** | 💬 Subtitles | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 6767)**: Automatic subtitle downloading in preferred languages for Jellyfin media libraries. |
| **Lidarr** | 🎵 Music Automation | ❌ *Missing* | ⭐⭐⭐⭐ **Deploy (Port 8686)**: Automated artist discography tracking and downloading for Navidrome (`/mnt/storage/Media/Music`). |
| **qBittorrent** | 📥 Downloader | ✅ **Active (8085)** | 24/7 background torrent downloader directly mapped to `/mnt/storage/Downloads`. |
| **FileBrowser** | 📁 Storage UI | ✅ **Active (8082)** | Managed web root at `/mnt/storage`. |
| **Vaultwarden** | 🔐 Password Vault | ✅ **Active (8083)** | Self-hosted Bitwarden-compatible password vault. |
| **Immich** | 📸 Photos & Videos | ✅ **Active (2283)** | Multi-user isolated photo cloud on `/mnt/storage/Media/Immich`. |
| **Portainer CE** | 🐳 Docker UI | ✅ **Active (9443)** | Container management and monitoring. |
| **Uptime Kuma** | 📈 Service Monitor | ✅ **Active (3001)** | Ping and HTTP health checks. |
| **AdGuard Home** | 🛡️ DNS Ad-Blocker | ✅ **Active (8053/53)**| Active network-wide DNS ad-blocker (superior alternative to Pi-Hole). |
| **Tailscale** | 🌐 Mesh VPN | ✅ **Active (Host)** | Encrypted global mesh VPN with MagicDNS (zero-config alternative to Twingate). |
| **Docmost** | 📚 Knowledge Base | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 3002)**: Modern collaborative wiki and Notion alternative for homelab documentation and personal notes. |
| **Hoarder** | 🔖 AI Bookmark App | ❌ *Missing* | ⭐⭐⭐⭐⭐ **Deploy (Port 3030)**: AI-assisted bookmarking, article saving, and full-text search engine. |
| **Home Assistant** | 🏡 Smart Home Hub | ❌ *Missing* | ⭐⭐⭐⭐ **Deploy (Port 8123)**: Central smart home automation engine and device dashboard. |
| **Prometheus + Node Exporter + Grafana** | 📈 Infrastructure Telemetry | ❌ *Missing* | ⭐⭐⭐⭐ **Deploy (3005/9090/9100)**: Deep server telemetry (CPU temps, NVENC load, disk I/O, network bandwidth). |
| **OctoPrint / TeslaMate / Frigate** | 🔬 Niche Hardware | ⏸️ *Hardware Dependent* | Documented for future hardware addition (3D printer USB, Tesla API, RTSP CCTV cameras). |

---

## 🏗️ Storage & Port Allocation Blueprint

All persistent data strictly follows the `/mnt/storage` architecture:

```
/mnt/storage/
├── AppData/
│   ├── services/           # Master Docker Compose stack
│   ├── glance/             # Glance configuration & dashboard YAML
│   ├── jellyseerr/         # Jellyseerr request database & cache
│   ├── prowlarr/           # Prowlarr indexer configurations
│   ├── radarr/             # Radarr movie database & metadata
│   ├── sonarr/             # Sonarr TV show database & metadata
│   ├── bazarr/             # Bazarr subtitle configuration & providers
│   ├── lidarr/             # Lidarr music database & metadata
│   ├── docmost/            # Docmost database, uploads, and data
│   ├── hoarder/            # Hoarder app data, Meilisearch index, and Redis
│   ├── homeassistant/      # Home Assistant configurations & blueprints
│   ├── prometheus/         # Prometheus time-series database
│   └── grafana/            # Grafana dashboards & plugins
├── Media/
│   ├── Movies/             # Managed by Radarr & streamed via Jellyfin
│   ├── TV/                 # Managed by Sonarr & streamed via Jellyfin
│   ├── Music/              # Managed by Lidarr & streamed via Navidrome
│   ├── Audiobooks/         # Audiobookshelf
│   └── Immich/             # User photo libraries
└── Downloads/
    ├── incomplete/         # Active qBittorrent downloads
    └── complete/           # Ingest folder for Radarr/Sonarr/Lidarr
```

### Dedicated Non-Conflicting Port Map

| Service | Port | Protocol | Purpose | Access URL |
| :--- | :--- | :--- | :--- | :--- |
| **Glance Dashboard** | `8088` | TCP | Homelab Startpage | `http://homeserver:8088` |
| **Jellyseerr** | `5055` | TCP | Media Discovery & Requests | `http://homeserver:5055` |
| **Prowlarr** | `9696` | TCP | Unified Tracker / Indexer Sync | `http://homeserver:9696` |
| **Radarr** | `7878` | TCP | Movie Automation | `http://homeserver:7878` |
| **Sonarr** | `8989` | TCP | TV Show Automation | `http://homeserver:8989` |
| **Bazarr** | `6767` | TCP | Subtitle Automation | `http://homeserver:6767` |
| **Lidarr** | `8686` | TCP | Music Automation | `http://homeserver:8686` |
| **Docmost** | `3002` | TCP | Knowledge Base & Wiki | `http://homeserver:3002` |
| **Hoarder** | `3030` | TCP | AI Bookmark & Content Hoarder | `http://homeserver:3030` |
| **Home Assistant** | `8123` | TCP | Smart Home Hub | `http://homeserver:8123` |
| **Grafana** | `3005` | TCP | Metrics Visualization | `http://homeserver:3005` |
| **Prometheus** | `9090` | TCP | Time-Series Metrics | `http://homeserver:9090` |
| **Node Exporter** | `9100` | TCP | Host Hardware Metrics | `http://homeserver:9100` |

---

## 🚀 Execution Roadmap

1. **Step 1: Directory Scaffolding & Permissions**: Create all necessary directories under `/mnt/storage/AppData/` and `/mnt/storage/Media/` with proper permissions (`1000:1000`).
2. **Step 2: Media Automation Stack Deployment**: Deploy `jellyseerr`, `prowlarr`, `radarr`, `sonarr`, `bazarr`, and `lidarr` into the master Docker Compose stack.
3. **Step 3: Productivity & Knowledge Apps Deployment**: Deploy `docmost` and `hoarder` with persistent storage.
4. **Step 4: Smart Home & Telemetry Deployment**: Deploy `homeassistant`, `prometheus`, `node-exporter`, and `grafana`.
5. **Step 5: Glance Dashboard Customization**: Configure `glance.yml` with all active service shortcuts, hardware monitoring widgets, weather, and RSS feeds.
6. **Step 6: Documentation & Verification**: Update `SELF_HOSTED_APPS.md` and `HOMESERVER_GUIDE.md`, verify health of all running containers, and test service availability over LAN and Tailscale.
