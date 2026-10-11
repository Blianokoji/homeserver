# 🏠 Homeserver Master Guide & Upgrade Log

This document is the **Single Source of Truth** for the system architecture, access points, maintenance procedures, and upgrade history of this headless home server.

> **Self-Hosted Applications Directory & Port Management**: For the dedicated catalog, container configurations, and credentials for all installed apps, see [`SELF_HOSTED_APPS.md`](~/SELF_HOSTED_APPS.md) and [`PORTEXPLAIN_REGISTRY.md`](~/PORTEXPLAIN_REGISTRY.md). Run [`portexplain`](~/.local/bin/portexplain) in terminal for a real-time listening socket & hit list breakdown, and [`caddy-proxies`](~/.local/bin/caddy-proxies) to inspect, monitor, and test all Caddy container reverse proxies.

---

## 🖥️ System Hardware & OS Overview

| Component | Specification | Notes |
| :--- | :--- | :--- |
| **Hostname** | `homeserver` | Resolves locally and via Tailscale MagicDNS |
| **Operating System** | Arch Linux (Kernel 7.1.x x86_64) | Headless Wayland/Hyprland configuration |
| **CPU** | Intel Core i3-6100 (2 Cores, 4 Threads @ 3.70 GHz) | Low idle power draw |
| **RAM** | 16 GB DDR4 | Memory available for containers and transcoding |
| **GPU** | NVIDIA GeForce GTX 1050 Ti (4 GB VRAM) | Hardware NVENC/NVDEC encoding & CUDA runtime |
| **OS Drive** | 120 GB SSD (`/dev/sda2` mounted on `/`) | Boot & Core System |
| **Storage Drive** | 1 TB Drive (`/dev/sdb1` mounted on `/mnt/storage`) | AppData, Media, Downloads, Backups |
| **Network Interface** | `enp2s0` (Gigabit Ethernet) | Static/DHCP: `<lan-ip>` |

---

## 🌐 Quick Access & Port Reference

| Service | Access URL | Port | Default Credentials / Method |
| :--- | :--- | :--| **Caddy Reverse Proxy** | [https://homeserver](https://homeserver) or [https://<lan-ip>](https://<lan-ip>) | `80`, `443` | Reverse proxy & automated local TLS gateway |
| **Glance Dashboard** | [http://homeserver:8088](http://homeserver:8088) or [http://<lan-ip>:8088](http://<lan-ip>:8088) | `8088` | Configured via `glance.yml` |
| **Immich (Photos & Videos Cloud)** | [http://homeserver:2283](http://homeserver:2283) or [http://<lan-ip>:2283](http://<lan-ip>:2283) | `2283` | Create admin account on first visit |
| **Jellyfin (Media Streaming)** | [http://homeserver:8096](http://homeserver:8096) or [http://<lan-ip>:8096](http://<lan-ip>:8096) | `8096` | Initial setup wizard on first visit (NVENC enabled) |
| **Jellyseerr (Media Requests)** | [http://homeserver:5055](http://homeserver:5055) or [http://<lan-ip>:5055](http://<lan-ip>:5055) | `5055` | Sign in with Jellyfin account |
| **Prowlarr (Tracker/Indexer Sync)** | [http://homeserver:9696](http://homeserver:9696) or [http://<lan-ip>:9696](http://<lan-ip>:9696) | `9696` | Setup credentials in Settings |
| **FlareSolverr (Cloudflare Proxy)** | [http://homeserver:8191](http://homeserver:8191) or [http://<lan-ip>:8191](http://<lan-ip>:8191) | `8191` | REST API on port 8191 |
| **Radarr (Movie Automation)** | [http://homeserver:7878](http://homeserver:7878) or [http://<lan-ip>:7878](http://<lan-ip>:7878) | `7878` | Setup credentials in Settings |
| **Sonarr (TV Automation)** | [http://homeserver:8989](http://homeserver:8989) or [http://<lan-ip>:8989](http://<lan-ip>:8989) | `8989` | Setup credentials in Settings |
| **Bazarr (Subtitles)** | [http://homeserver:6767](http://homeserver:6767) or [http://<lan-ip>:6767](http://<lan-ip>:6767) | `6767` | Setup credentials in Settings |
| **Lidarr (Music Automation)** | [http://homeserver:8686](http://homeserver:8686) or [http://<lan-ip>:8686](http://<lan-ip>:8686) | `8686` | Setup credentials in Settings |
| **qBittorrent (Downloads)** | [http://homeserver:8085](http://homeserver:8085) or [http://<lan-ip>:8085](http://<lan-ip>:8085) | `8085` | Default: Initial setup wizard |
| **Docmost (Knowledge Base)** | [http://homeserver:3002](http://homeserver:3002) or [http://<lan-ip>:3002](http://<lan-ip>:3002) | `3002` | Create admin account on first visit |
| **Hoarder (AI Bookmark App)** | [http://homeserver:3030](http://homeserver:3030) or [http://<lan-ip>:3030](http://<lan-ip>:3030) | `3030` | Create admin account on first visit |
| **Home Assistant (Smart Home)** | [http://homeserver:8123](http://homeserver:8123) or [http://<lan-ip>:8123](http://<lan-ip>:8123) | `8123` | Onboarding wizard on first visit |
| **Vaultwarden (Password Manager)**| [http://homeserver:8083](http://homeserver:8083) or [http://<lan-ip>:8083](http://<lan-ip>:8083) | `8083` | Create master vault account on first visit |
| **FileBrowser (Storage Manager)** | [http://homeserver:8082](http://homeserver:8082) or [http://<lan-ip>:8082](http://<lan-ip>:8082) | `8082` | Default: Initial setup wizard |
| **Audiobookshelf (Audiobooks/Podcasts)** | [http://homeserver:13378](http://homeserver:13378) or [http://<lan-ip>:13378](http://<lan-ip>:13378)| `13378`| Create root account on first visit |
| **Navidrome (Music Streaming)** | [http://homeserver:4533](http://homeserver:4533) or [http://<lan-ip>:4533](http://<lan-ip>:4533) | `4533` | Create admin account on first visit |
| **Uptime Kuma (Status & Monitoring)** | [http://homeserver:3001](http://homeserver:3001) or [http://<lan-ip>:3001](http://<lan-ip>:3001) | `3001` | Create admin account on first visit |
| **AdGuard Home (DNS & Ad-Blocker)** | [http://homeserver:8053](http://homeserver:8053) or [http://<lan-ip>:8053](http://<lan-ip>:8053) | `8053` / `53` | Active DNS filtering & Web UI |
| **Grafana (Metrics Dashboard)** | [http://homeserver:3005](http://homeserver:3005) or [http://<lan-ip>:3005](http://<lan-ip>:3005) | `3005` | User: `admin` \| Password: `admin` |
| **Prometheus (Telemetry Engine)** | [http://homeserver:9090](http://homeserver:9090) or [http://<lan-ip>:9090](http://<lan-ip>:9090) | `9090` | Open Metrics Console |
| **CasaOS Dashboard** | [http://homeserver](http://homeserver) or [http://<lan-ip>](http://<lan-ip>) | `80` | Initial setup on first visit |
| **IPTV Live TV Gateway** | [http://homeserver:8484](http://homeserver:8484) or [http://<lan-ip>:8484](http://<lan-ip>:8484) | `8484` | M3U Tuner & stream proxy for Jellyfin Live TV |
| **CopyPop (File & Clipboard Sync)** | [http://homeserver:18080](http://homeserver:18080) or [http://<lan-ip>:18080](http://<lan-ip>:18080) | `18080` | Passkey: Configured via environment variable \| Drops uploads into storage |
| **Portainer CE** | [https://homeserver:9443](https://homeserver:9443) | `9443` | Create admin account on first visit |
| **Sunshine Admin** | [https://homeserver:47990](https://homeserver:47990) | `47990` | Create admin credentials on first visit |
| **CUPS & AirPrint (Print Server)** | [http://homeserver:631](http://homeserver:631) \| [WebPrint: 8084](http://homeserver:8084) | `631`, `8084` | Configured via `CUPS_USER` & `CUPS_PASSWORD` |
| **SearXNG (Metasearch Engine)** | [http://homeserver:8080](http://homeserver:8080) or [http://<lan-ip>:8080](http://<lan-ip>:8080) | `8080` | Privacy-first metasearch & agent JSON search API |
| **Ollama (Local LLM Inference)** | [http://homeserver:11434](http://homeserver:11434) or [http://<lan-ip>:11434](http://<lan-ip>:11434) | `11434` | Local GPU-accelerated LLM API (GTX 1050 Ti) |
| **Moonlight Streaming** | Connect via Moonlight app to `homeserver` | `47984-48010` | Pair with 4-digit PIN via Sunshine Web UI |
| **Tailscale Admin** | [https://login.tailscale.com/admin](https://login.tailscale.com/admin) | N/A | Authenticated via Tailscale account |

---

## ⚙️ Core Architecture & Configurations

### 1. 24/7 Headless Reliability & Sleep Prevention
* **Systemd Targets Masked**:
  ```bash
  sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
  ```
* **Hypridle Power Management**:
  * Config path: `~/.config/hypr/hypridle.conf`
  * System suspend actions are removed to prevent sleep on inactivity.
* **Motherboard BIOS Setting (Crucial for Power Outages)**:
  * In BIOS setup (*Gigabyte H110M*): Set **AC Back / Restore on AC Power Loss** to **`Always On`** or **`Memory`** so the server powers on automatically when electricity returns.

---

### 2. Headless Auto-Boot & DRM Virtual Layer
* **TTY1 Auto-login**:
  * Config path: `/etc/systemd/system/getty@tty1.service.d/autologin.conf`
  * Automatically authenticates the host user on boot without requiring a physical keyboard or display.
* **Shell Auto-Start**:
  * Config path: `~/.bash_profile`
  * Boots `start-hyprland` automatically when logged into `tty1`.
* **Kernel-Level DRM Virtual Layer**:
  * Eliminates volatile compositor-level headless hacks in favor of kernel-managed DRM interfaces:
    1. **VKMS (Virtual Kernel Mode Setting)**:
       * Module configuration: `/etc/modules-load.d/vkms.conf` & `/etc/modprobe.d/vkms.conf`
       * Provides a native virtual DRM device (`/dev/dri/cardX`, connector `Virtual-1` / `VKMS-1`) directly to Aquamarine / Hyprland and Sunshine.
    2. **Kernel DRM EDID Forcing (`drm.edid_firmware` & `video=...:e`)**:
       * Stores custom 1080p EDID in `/usr/lib/firmware/edid/1080p.bin`.
       * Kernel parameter in GRUB: `drm.edid_firmware=HDMI-A-1:edid/1080p.bin video=HDMI-A-1:1920x1080@60e`
       * Forces the NVIDIA GTX 1050 Ti DRM connector (`HDMI-A-1`) to remain permanently connected with hardware NVENC acceleration even without a physical monitor.
    3. **Hardware HDMI Dummy Plug**:
       * Low-cost hardware termination plug simulating an active monitor connection on the GPU.

---

### 3. Worldwide Remote Access (Tailscale Mesh VPN)
* **Status / Service**: `tailscaled.service` (enabled on boot)
* **Initial Connection Command**:
  ```bash
  sudo tailscale up --ssh --operator=$USER
  ```
* **Capabilities**:
  * **Zero Router Port Forwarding**: Access the server securely behind CGNAT, mobile hotspots, or guest Wi-Fi networks.
  * **MagicDNS**: Access services by name: `http://homeserver`, `ssh <user>@homeserver`.
  * **Tailscale SSH**: Seamless SSH login directly from mobile or desktop terminals.

---

### 4. Hardware-Accelerated Remote Desktop (Sunshine + Moonlight)
* **Package**: `sunshine-bin` (AUR)
* **Service**: `systemctl --user status sunshine`
* **GPU Acceleration**: Utilizes NVIDIA GTX 1050 Ti NVENC encoder for low-latency, 60+ FPS desktop streaming.
* **Udev Rule**: `/etc/udev/rules.d/85-sunshine-input.rules` (allows virtual mouse/keyboard/gamepad input via `uinput`).
* **KMS Capabilities**: `sudo setcap cap_sys_admin+ep /usr/bin/sunshine`
* **Client Pairing Instructions**:
  1. Open **Moonlight** on client device (iOS / Android / Mac / Windows / Linux).
  2. Click **Add Host** -> Type `homeserver` (or Tailscale IP).
  3. Moonlight displays a 4-digit PIN.
  4. Open browser to `https://homeserver:47990` -> **PIN** tab -> Enter PIN -> Click **Send**.
  5. Select **Desktop** in Moonlight to stream your screen.

---

### 5. Storage Layout (`/mnt/storage`)
All persistent app data, media files, and container volumes are structured under `/mnt/storage`:
```
/mnt/storage/
├── AppData/       # Docker persistent configs and databases
│   ├── services/  # Master docker-compose.yml (Jellyfin, qBit, Vaultwarden, etc.)
│   ├── immich/    # Immich database (postgres), config (.env), and model cache
│   ├── jellyfin/  # Jellyfin config and transcode cache
│   ├── qbittorrent/# qBittorrent config
│   ├── vaultwarden/# Vaultwarden encrypted database
│   ├── filebrowser/# FileBrowser SQLite database and settings
│   ├── audiobookshelf/# Audiobookshelf config and metadata
│   ├── navidrome/ # Navidrome database and cache
│   ├── uptime-kuma/# Uptime Kuma database
│   ├── adguardhome/# AdGuard Home DNS config and filters
│   └── portainer/ # Portainer CE persistent data
├── Media/         # Media libraries & Cloud Uploads
│   ├── Immich/    # User photos and videos (segregated into library/<user>/...)
│   ├── Movies/    # Movie files (streamed by Jellyfin)
│   ├── TV/        # TV Show episodes (streamed by Jellyfin)
│   ├── Music/     # Music albums (streamed by Navidrome & Jellyfin)
│   ├── Audiobooks/# Audiobooks (streamed by Audiobookshelf)
│   └── Podcasts/  # Podcasts (managed by Audiobookshelf)
├── Downloads/     # Incomplete & completed torrent / direct downloads
└── Backups/       # Snapshot backups and system archives
```

---

### 6. Docker & NVIDIA Container Toolkit
* **Service**: `docker.service` (enabled on boot)
* **NVIDIA Runtime Config**:
  ```bash
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  ```
* **Self-Hosted App Stack**:
  * **CasaOS**: Web UI on port `80` with a 1-click app store (Nextcloud, Jellyfin, Vaultwarden, AdGuard Home, Immich, etc.).
  * **Portainer CE**: Advanced Docker container and compose management on `https://homeserver:9443`.

---

### 7. Self-Hosted Photos & Videos Cloud (Immich)
* **Access URL**: [http://homeserver:2283](http://homeserver:2283) or [http://<lan-ip>:2283](http://<lan-ip>:2283) (accessible locally and remotely via Tailscale)
* **Stack Path**: `/mnt/storage/AppData/immich/docker-compose.yml`
* **Restart Policy**: `restart: always` (ensures 24/7 continuous operation across reboots or crashes).
* **Multi-User Isolation & HDD Storage Separation**:
  * **Private User Accounts**: Each user (you, your dad, family members) creates or is assigned an isolated Immich account. Photos, albums, and timelines are private by default.
  * **HDD Separate Folder Storage Template**:
    * Configure via **Immich Web UI** -> **Administration (Gear icon)** -> **Settings** -> **Storage Template**.
    * Enable **Storage Template** and set format:
      `{{user.name}}/{{y}}/{{MM}}/{{filename}}`
    * Uploaded media on the 1TB hard drive will automatically be saved into segregated directories:
      * `/mnt/storage/Media/Immich/library/<username>/2026/08/IMG_001.jpg`
      * `/mnt/storage/Media/Immich/library/dad/2026/08/IMG_002.jpg`
* **Connecting Mobile Devices (iOS / Android)**:
  1. Install the **Immich** app from the App Store / Google Play.
  2. Server URL: `http://homeserver:2283` (with Tailscale active) or `http://<lan-ip>:2283` (on home Wi-Fi).
  3. Log in with the respective user's credentials.
  4. Enable **Backup** / **Auto-Sync** for camera roll.

---

## 🛠️ Maintenance & Administration Playbook

### 1. Updating System Packages (Arch Linux)
Run maintenance updates once every 1–2 weeks:
```bash
# Update Arch core packages and AUR packages
yay -Syu

# Clean pacman cache to free up SSD space
sudo pacman -Sc
```

### 2. Updating Docker Containers
* **Via CasaOS UI**: Click the update badge next to any installed app.
* **Via Portainer UI**: Navigate to Containers -> Recreate -> Pull latest image.
* **Via Command Line (for Compose stacks)**:
  ```bash
  cd /mnt/storage/AppData/<app-folder>
  docker compose pull
  docker compose up -d --remove-orphans
  ```

### 3. Checking DRM Virtual Layer & Remote Desktop
If the remote screen does not respond or you need to inspect DRM displays:
```bash
# Check DRM cards and connectors recognized by kernel
ls -l /sys/class/drm/

# Check monitors recognized by Hyprland
hyprctl monitors

# Restart Sunshine service if needed
systemctl --user restart sunshine
```

### 4. Adding a New Hard Drive / Storage Expansion
1. Connect drive and identify device name:
   ```bash
   lsblk -f
   ```
2. Create filesystem (if new):
   ```bash
   sudo mkfs.ext4 -L "Storage2" /dev/sdX1
   ```
3. Create mount point and add to `/etc/fstab`:
   ```bash
   sudo mkdir -p /mnt/storage2
   # Add entry using UUID:
   UUID=<your-uuid>  /mnt/storage2  ext4  rw,relatime  0 2
   ```
4. Set permissions:
   ```bash
   sudo chown -R $USER:$USER /mnt/storage2
   sudo chmod -R 775 /mnt/storage2
   ```

### 5. Automated Backups of AppData
To create a timestamped backup of all container configurations:
```bash
sudo tar -czvf /mnt/storage/Backups/appdata_backup_$(date +%Y%m%d).tar.gz /mnt/storage/AppData
```

---

## 📋 Upgrade & Modification History Log

*Use this section to record any future hardware upgrades, system modifications, or newly deployed services.*

| Date (YYYY-MM-DD) | Change Category | Description of Change / Upgrade | Author / Notes |
| :--- | :--- | :--- | :--- |
| **2026-08-22** | **Initial Setup** | Configured headless 24/7 server, sleep prevention, TTY1 autologin, Tailscale mesh VPN, Sunshine/Moonlight remote desktop, `/mnt/storage` hierarchy, CasaOS, and Portainer CE. | SysAdmin |
| **2026-08-22** | **DRM Virtual Layer** | Removed compositor-level Hyprland headless monitor hacks (`ensure_display.sh`, `HEADLESS-1`). Migrated to kernel-level DRM Virtual Layer (VKMS & Kernel EDID DRM injection). | SysAdmin |
| **2026-08-29** | **TechHut 2025 Homelab Expansion** | Deployed full *arr media automation ecosystem (Jellyseerr, Prowlarr, Radarr, Sonarr, Bazarr, Lidarr), Glance unified dashboard, Docmost knowledge base, Hoarder AI bookmarking, Home Assistant smart home hub, and Prometheus/Node Exporter/Grafana telemetry suite. | SysAdmin |
| **2026-08-30** | **Media Pipeline & Queue Optimization** | Configured global zero-seeding limits on qBittorrent (`GlobalMaxRatio=0`, `GlobalMaxSeedingMinutes=0`) to prevent completed downloads from blocking the request queue. Expanded active slots to 10 parallel downloads. Linked Jellyfin automatic library update webhooks in Radarr/Sonarr, resolved unindexed media (The Furious), and activated multi-source search fallback for rare requests. | SysAdmin |
| **2026-09-06** | **Jellyseerr Delete Requested Engine** | Implemented custom 'Delete Requested' automation (`custom-delete-requested.js` + `apply-patches.sh`) in Jellyseerr container to pause active torrents, delete torrent data from qBittorrent, purge leftover downloads from `/downloads`, remove series/movies from Sonarr/Radarr, and reset Jellyseerr request/media records. Added `/mnt/storage/Downloads` mount and [`jellyseerr-delete-requested`](~/.local/bin/jellyseerr-delete-requested) CLI utility. Removed stalled Shin Chan download and reclaimed 17 GB storage. | SysAdmin |
| **2026-09-06** | **Caddy Reverse Proxy Auditor CLI** | Deployed [`caddy-proxies`](~/.local/bin/caddy-proxies) (with `caddyproxies` and `caddy-routes` symlinks) in `~/.local/bin`. Interrogates the Caddy container via Admin API (with offline Caddyfile fallback), audits ingress domains, access policies (Admin vs Public), backend container health, and offers active upstream reachability probing (`--check`), search filtering, and JSON export. | SysAdmin |
| **2026-09-07** | **IPTV Live TV Gateway for Jellyfin** | Built and deployed ultra-lightweight Docker container (`homeserver/iptv-proxy` on port 8484, ~26MB RAM) to filter and proxy `iptv-org` M3U channels with verified `tvg-logo` icons and browser User-Agent injection. Connected Jellyfin Live TV Tuner directly to `http://iptv-proxy:8484/playlist.m3u` with NVENC hardware acceleration, populating 400+ channels with logos. Added Caddy reverse proxy at `iptv.<tailscale-domain>` and registered in `services.json`. | SysAdmin |
| **2026-09-07** | **CopyPop Autostart & Service Registration** | Configured `copypop.service` user systemd unit with correct Node.js binary path (`~/.local/bin/node`), installed project dependencies via npm, enabled persistent boot autostart via systemd linger, added `enable`/`disable` subcommands to `~/.local/bin/copypop`, and registered port `18080` across portexplain and system documentation. | SysAdmin |
| **2026-09-21** | **Jellyfin Mobile Responsive UI & Seamless UX Engine (v2.0)** | Re-engineered Jellyfin custom CSS (`branding.xml`) with an ultra-responsive UX engine. Resolved popup/dialog/action-sheet sticking by removing `!important` animation overrides that paralyzed JavaScript's `animationend` exit event loop. Enforced absolute hide specificity (`.hide`, `#loginPage.hide`, `.dialog.hide` -> `display: none !important`) so inactive login cards/backdrops never persist or obscure detail views. Engineered browser-level DOM virtualization/memoization using `content-visibility: auto` and layout containment on cards/lists for 120fps touch scrolling. Re-architected X/Y/Z-axis stacking, flexbox alignment, and multi-viewport media queries across phones, tablets, foldables, and desktops. | SysAdmin |
| **2026-09-21** | **Multi-Source Live TV Compilation & Resilient EPG Engine** | Upgraded `iptv-proxy` (port 8484) to compile 10 legal free-to-air & open-source sources (Malayalam priority, Free-TV India & Global, News, Sports, Movies, Kids, Documentary, Music) concurrently via thread pool (5,500+ channels). Implemented atomic cache write invariants to prevent empty playlist wipes on upstream network blips, fixed Jellyfin numeric channel stripping bug (e.g. 24 News -> 24 News HD), and integrated a 24/7 categorized XMLTV EPG schedule engine. Synchronized tuners and guides into Jellyfin Live TV. | SysAdmin |
| **2026-09-28** | **Jellyfin v12 Upgrade & CSS Reset** | Upgraded Jellyfin from `latest` (was auto-tracking) to the explicit `jellyfin/jellyfin:12` tag (v12.1 — released 2026-09-07) in [`docker-compose.yml`](file:///mnt/storage/AppData/services/docker-compose.yml). Completely wiped all custom JellySkin CSS and the "Ultra-Responsive Mobile UX Engine" from [`branding.xml`](file:///mnt/storage/AppData/jellyfin/config/config/branding.xml) — reverted to stock Jellyfin default theme to eliminate layout breakage, dialog-sticking, and incompatibility issues with official Jellyfin iOS/Android/TV apps. Previous CSS backed up as `branding.xml.backup.20260928_*`. | SysAdmin |
| **2026-09-28** | **Movie Pipeline Latency Audit & NVENC Fix** | Full pipeline audit (live FFmpeg log analysis, encoding.xml, system.xml, network.xml, Caddy, Radarr) revealed Jellyfin was using **software CPU transcoding (`libx264`) at 0.42× real-time** (324% CPU / 3× OOM-kill `FFmpeg code 137` crashes during 4K HEVC HDR playback), completely ignoring the GTX 1050 Ti GPU. **Root causes fixed:** (1) `HardwareAccelerationType` → `nvenc` in [`encoding.xml`](file:///mnt/storage/AppData/jellyfin/config/config/encoding.xml) — enables full NVENC/NVDEC+CUDA pipeline. (2) Expanded `HardwareDecodingCodecs` to `hevc, mpeg2video, mpeg4, vc1, vp9, vp8` (was only `h264, vc1`). (3) `EnableTonemapping=true` + `EnableHardwareEncoding=true` + `AllowHevcEncoding=true`. (4) Transcode throttling (180s) and segment deletion (720s) enabled. (5) Caddy `read_buffer` 8 KB → 4 MB in [`10-media.caddy`](file:///mnt/storage/AppData/caddy/conf.d/10-media.caddy); streaming-safe timeouts; static asset `Cache-Control: immutable`. (6) `KnownProxies` in [`network.xml`](file:///mnt/storage/AppData/jellyfin/config/config/network.xml) populated with `172.25.0.0/16` (caddy_proxy subnet) so Jellyfin records real client IPs instead of Caddy's internal Docker IP. (7) `TrickplayOptions.EnableHwAcceleration=true` + `EnableHwEncoding=true` in [`system.xml`](file:///mnt/storage/AppData/jellyfin/config/config/system.xml) — scrubber thumbnail strips now generated via NVENC instead of CPU. (8) Radarr `LogLevel` `debug` → `info` in [`config.xml`](file:///mnt/storage/AppData/radarr/config.xml) to stop continuous debug disk I/O. Cleared stale transcode cache. TV library (`/media/TV`) confirmed empty (no content yet) — not a mount error. Expected: transcode speed 0.42× → 5–15× real-time; CPU per 4K stream 324% → ~20%. | SysAdmin |


---

## 🆘 Quick Troubleshooting Cheat Sheet

| Symptom | Probable Cause | Fix |
| :--- | :--- | :--- |
| **Cannot SSH from outside home** | Tailscaled is inactive or needs login | Run `sudo tailscale status` or `sudo tailscale up --ssh` |
| **No display detected on headless boot** | DRM connector not forced or VKMS module unloaded | Verify `/sys/class/drm` or load VKMS (`sudo modprobe vkms`) |
| **Sunshine PIN not showing** | Sunshine user service not running | Run `systemctl --user restart sunshine` |
| **CasaOS not loading** | Port 80 conflict or Docker daemon stopped | Run `sudo systemctl status docker` and `sudo systemctl restart casaos` |
| **Permission denied in `/mnt/storage`** | Ownership not set to user | Run `sudo chown -R $USER:$USER /mnt/storage` |
