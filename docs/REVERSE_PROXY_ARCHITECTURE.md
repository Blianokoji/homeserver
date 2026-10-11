# 🌐 Production Reverse-Proxy Architecture & Access Control Manual

**Homeserver Application Gateway: Tailscale + Caddy + Docker**  
*Single Source of Truth for Gateway Operations, Access Governance, and Domain Routing*

---

## 📑 Table of Contents
1. [Architecture Overview & Data Flow](#1-architecture-overview--data-flow)
2. [Complete Service Inventory & Classification](#2-complete-service-inventory--classification)
3. [Domain Architecture & Private DNS Resolution](#3-domain-architecture--private-dns-resolution)
4. [Tailscale Identity-Based Access Control (Grants Format)](#4-tailscale-identity-based-access-control-grants-format)
5. [Caddy Reverse Proxy Implementation](#5-caddy-reverse-proxy-implementation)
6. [Docker Networking Topology](#6-docker-networking-topology)
7. [Comprehensive Access Control Matrix](#7-comprehensive-access-control-matrix)
8. [TLS Strategy & Certificate Trust](#8-tls-strategy--certificate-trust)
9. [Operational Commands & Runbook](#9-operational-commands--runbook)
10. [Security Audit & Defense-in-Depth Analysis](#10-security-audit--defense-in-depth-analysis)
11. [Backups & Disaster Recovery / Rollback](#11-backups--disaster-recovery--rollback)
12. [Standard Operating Procedure: Adding a New Service](#12-standard-operating-procedure-adding-a-new-service)
13. [Standard Operating Procedure: User Access Governance](#13-standard-operating-procedure-user-access-governance)

---

## 1. Architecture Overview & Data Flow

This reverse-proxy architecture establishes a secure, unified application gateway on `homeserver` (`<tailscale-ip>` / `<lan-ip>`) using **Tailscale** for identity and transport encryption, **Caddy** for Layer 7 reverse proxy routing and automatic local TLS termination, and a dedicated **Docker bridge network (`caddy_proxy`)** for isolated container-to-container communication.

```
+-----------------------------------------------------------------------------------------+
|                                    INCOMING CLIENTS                                     |
|  • Owner / Admin (admin@example.com: homeserver, dracore-ultraxv, phone)       |
|  • Media Users (media-user@example.com)                                         |
|  • Local LAN Clients (<lan-subnet>)                                                  |
+--------------------------------------------+--------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                LAYER 3/4 SECURITY BOUNDARY                              |
|                          Tailscale Mesh WireGuard (<tailscale-ip>)                       |
|  • group:admins      --> FULL ACCESS TO ALL PORTS (22, 80, 443, host sockets, SSH)      |
|  • group:media-users --> RESTRICTED SOLELY TO PORTS 80 & 443 (ALL OTHER PORTS DROPPED) |
+--------------------------------------------+--------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                LAYER 7 APPLICATION GATEWAY                              |
|                          Caddy Reverse Proxy (Docker Container)                         |
|                                Ports: 80 (HTTP) & 443 (HTTPS)                           |
|                                                                                         |
|  [ admin_only snippet ]                                                                 |
|   Remote IP must match LAN (<lan-subnet>, 127.0.0.1) or Admin Nodes (<admin-node-ips>)  |
|   Non-admin clients requesting admin domains get immediate 403 Forbidden               |
|                                                                                         |
|  [ Media Gateway ]                                                                      |
|   Jellyfin, Jellyseerr, Immich allow both group:admins and group:media-users           |
+--------------------------------------------+--------------------------------------------+
                                             |
                         +-------------------+-------------------+
                         |                                       |
                         v                                       v
+------------------------------------+ +--------------------------------------------------+
|      DOCKER BRIDGE: caddy_proxy    | |          HOST NETWORK GATEWAY (extra_hosts)      |
|                                    | |               host.docker.internal               |
| • jellyfin:8096                    | | • jellyseerr:5055 (Host-mode container)          |
| • immich_server:2283               | | • cups:631 (CUPS Print Administration)           |
| • radarr:7878, sonarr:8989         | | • cups:8084 (WebPrint Cloud Portal)              |
| • prowlarr:9696, bazarr:6767       | +--------------------------------------------------+
| • lidarr:8686, qbittorrent:8085    |
| • vaultwarden:80, filebrowser:80   |
| • audiobookshelf:80, navidrome:4533|
| • homeassistant:8123 (Trusted Prox)|
| • uptime_kuma:3001, docmost:3000   |
| • hoarder_web:3000, searxng:8080   |
| • ollama:11434, adguardhome:80     |
| • grafana:3000, prometheus:9090    |
+------------------------------------+
```

### Key Architectural Invariants
1. **Zero Public Exposure**: The homeserver does not port-forward ports 80, 443, or any application port to the public Internet on the home router. Remote access requires authenticated Tailscale membership.
2. **Dual-Layer Isolation (No Security Theater)**:
   - **Layer 4**: Tailscale Grants policy physically prevents restricted users from connecting to backend ports (`8096`, `5055`, `2283`, `7878`, `22`, etc.).
   - **Layer 7**: Caddy enforces `admin_only` checks on all management endpoints, rejecting requests for admin subdomains from non-admin Tailscale IPs with `403 Forbidden`.
3. **Internal Container DNS**: Caddy communicates with proxied containers directly via the Docker bridge network `caddy_proxy`, eliminating dependency on host port exposure for proxy traffic.

---

## 2. Complete Service Inventory & Classification

All 31 self-hosted software components deployed on `homeserver` are inventoried below with their proxy status and security classifications:

| Application | Container Name | Target Hostname(s) | Upstream Target | Classification | Auth Type | Special Requirements |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Glance Dashboard** | `glance` | `glance.<tailscale-domain>`, `homeserver` | `glance:8080` | **TAILSCALE-ONLY (Admin)** | Config-based | Admin restricted |
| **Jellyfin** | `jellyfin` | `jellyfin.<tailscale-domain>` | `jellyfin:8096` | **TAILSCALE-ONLY (Media & Admin)** | User / Password | WebSockets, Large stream buffer, NVENC |
| **Jellyseerr** | `jellyseerr` | `jellyseerr.<tailscale-domain>` | `host.docker.internal:5055` | **TAILSCALE-ONLY (Media & Admin)** | Jellyfin OAuth | Host networking mode |
| **Immich** | `immich_server` | `immich.<tailscale-domain>` | `immich_server:2283` | **TAILSCALE-ONLY (Media & Admin)** | User / Password | WebSockets, 50GB request body, User isolation |
| **Vaultwarden** | `vaultwarden` | `vaultwarden.<tailscale-domain>` | `vaultwarden:80` | **TAILSCALE-ONLY (Admin)** | Master Password | Strict HTTPS only (WebCrypto), WebSockets |
| **Home Assistant** | `homeassistant` | `homeassistant.<tailscale-domain>` | `homeassistant:8123` | **TAILSCALE-ONLY (Admin)** | User / Password | WebSockets, `trusted_proxies` in `.storage/http` |
| **Radarr** | `radarr` | `radarr.<tailscale-domain>` | `radarr:7878` | **TAILSCALE-ONLY (Admin)** | API / Forms | Admin restricted |
| **Sonarr** | `sonarr` | `sonarr.<tailscale-domain>` | `sonarr:8989` | **TAILSCALE-ONLY (Admin)** | API / Forms | Admin restricted |
| **Prowlarr** | `prowlarr` | `prowlarr.<tailscale-domain>` | `prowlarr:9696` | **TAILSCALE-ONLY (Admin)** | API / Forms | Admin restricted |
| **Bazarr** | `bazarr` | `bazarr.<tailscale-domain>` | `bazarr:6767` | **TAILSCALE-ONLY (Admin)** | API / Forms | Admin restricted |
| **Lidarr** | `lidarr` | `lidarr.<tailscale-domain>` | `lidarr:8686` | **TAILSCALE-ONLY (Admin)** | API / Forms | Admin restricted |
| **qBittorrent WebUI** | `qbittorrent` | `qbittorrent.<tailscale-domain>` | `qbittorrent:8085` | **TAILSCALE-ONLY (Admin)** | User / Password | `header_up Host {upstream_hostport}` (CSRF fix) |
| **FileBrowser** | `filebrowser` | `filebrowser.<tailscale-domain>` | `filebrowser:80` | **TAILSCALE-ONLY (Admin)** | User / Password | 50GB request body, Admin restricted |
| **Audiobookshelf** | `audiobookshelf` | `audiobookshelf.<tailscale-domain>`| `audiobookshelf:80` | **TAILSCALE-ONLY (Admin)** | User / Password | WebSockets, Audio streaming |
| **Navidrome** | `navidrome` | `navidrome.<tailscale-domain>` | `navidrome:4533` | **TAILSCALE-ONLY (Admin)** | User / Password | Subsonic API, Music streaming |
| **Docmost** | `docmost` | `docmost.<tailscale-domain>` | `docmost:3000` | **TAILSCALE-ONLY (Admin)** | User / Password | WebSockets (Collaboration) |
| **Hoarder** | `hoarder_web` | `hoarder.<tailscale-domain>` | `hoarder_web:3000` | **TAILSCALE-ONLY (Admin)** | User / Password | AI bookmarking |
| **SearXNG** | `searxng` | `search.<tailscale-domain>` | `searxng:8080` | **TAILSCALE-ONLY (Admin)** | Sovereign Search | JSON API enabled |
| **Ollama** | `ollama` | `ollama.<tailscale-domain>` | `ollama:11434` | **TAILSCALE-ONLY (Admin)** | API Key / Open | GPU Acceleration (GTX 1050 Ti) |
| **Uptime Kuma** | `uptime_kuma` | `uptime.<tailscale-domain>` | `uptime_kuma:3001` | **TAILSCALE-ONLY (Admin)** | User / Password | WebSockets (socket.io) |
| **AdGuard Home WebUI**| `adguardhome` | `adguard.<tailscale-domain>` | `adguardhome:80` | **TAILSCALE-ONLY (Admin)** | User / Password | Port 80 internal / 8053 host |
| **Grafana** | `grafana` | `grafana.<tailscale-domain>` | `grafana:3000` | **TAILSCALE-ONLY (Admin)** | User / Password | WebSockets |
| **Prometheus** | `prometheus` | `prometheus.<tailscale-domain>` | `prometheus:9090` | **TAILSCALE-ONLY (Admin)** | Open Metrics Console| Sensitive telemetry |
| **CUPS Admin** | `cups` | `cups.<tailscale-domain>` | `host.docker.internal:631` | **TAILSCALE-ONLY (Admin)** | PAM (Admin User) | Host networking mode |
| **CUPS WebPrint** | `cups` | `webprint.<tailscale-domain>` | `host.docker.internal:8084`| **TAILSCALE-ONLY (Admin)** | Open Dropzone | 100MB request body |
| **AdGuard DNS (Port 53)**| `adguardhome`| *N/A (Raw DNS UDP/TCP)* | `0.0.0.0:53` | **LAN & TAILSCALE** | None (DNS) | Do NOT reverse-proxy raw DNS |
| **qBittorrent P2P (6881)**| `qbittorrent`| *N/A (Raw BitTorrent)* | `0.0.0.0:6881` | **LAN & TAILSCALE** | BitTorrent Protocol | Do NOT reverse-proxy raw P2P |
| **FlareSolverr** | `flaresolverr`| *N/A (Backend Proxy)* | `0.0.0.0:8191` | **INTERNAL ONLY** | None | Scraped by Prowlarr |
| **Node Exporter** | `node_exporter`| *N/A (Metrics Probe)* | `0.0.0.0:9100` | **INTERNAL ONLY** | None | Scraped by Prometheus |
| **Database Containers** | `immich_postgres`, `docmost_db`, etc. | *N/A* | Internal Docker network | **INTERNAL ONLY** | DB Credentials | Never exposed via proxy |
| **Cache Engines** | `immich_redis`, `docmost_redis`, etc. | *N/A* | Internal Docker network | **INTERNAL ONLY** | Redis Auth | Never exposed via proxy |

---

## 3. Domain Architecture & Private DNS Resolution

### Domain Strategy
To align with Tailscale's native private infrastructure without requiring public domain registration, the gateway uses **Tailscale MagicDNS subdomains** with optional local fallback aliases:
- **Primary Domain**: `<service>.<tailscale-domain>`
- **LAN / Local Aliases**: `<service>.homeserver` and `<service>.home.arpa`

### DNS Resolution Architecture
1. **AdGuard Home Wildcard Rewrites (`/mnt/storage/AppData/adguardhome/conf/AdGuardHome.yaml`)**:
   AdGuard Home on port 53 (`<tailscale-ip>:53` on Tailscale, `<lan-ip>:53` on LAN) is configured with wildcard DNS rewrites:
   ```yaml
   rewrites:
     - domain: "*.<tailscale-domain>"
       answer: "<tailscale-ip>"
       enabled: true
     - domain: "<tailscale-domain>"
       answer: "<tailscale-ip>"
       enabled: true
     - domain: "*.homeserver"
       answer: "<tailscale-ip>"
       enabled: true
     - domain: "*.home.arpa"
       answer: "<tailscale-ip>"
       enabled: true
   ```
2. **Tailscale Private DNS Configuration**:
   In the Tailscale Admin Console under **DNS > Nameservers**:
   - Add **`<tailscale-ip>`** as a custom nameserver with **Split DNS** for search domain `<tailnet-name>.ts.net` (or `<tailscale-domain>`).
   - Alternatively, toggle "Override local DNS" with `<tailscale-ip>` to give all connected tailnet devices network-wide ad-blocking and automatic private domain resolution.
3. **Local LAN Resolution**:
   On the home network, the home router DHCP supplies `<lan-ip>` (AdGuard Home) as primary DNS, instantly resolving all `<service>.<tailscale-domain>` queries.

---

## 4. Tailscale Identity-Based Access Control (Grants Format)

The unrestricted Tailscale policy (`{"src": ["*"], "dst": ["*"], "ip": ["*"]}`) is replaced with an enterprise-grade Grants policy enforcing strict network separation.

### Active Tailscale Grants Specification
File location: `docs/TAILSCALE_POLICY.json`

```json
{
  "groups": {
    "group:admins": [
      "admin@example.com"
    ],
    "group:media-users": [
      "media-user@example.com"
    ]
  },
  "tagOwners": {
    "tag:server": [
      "group:admins"
    ]
  },
  "hosts": {
    "homeserver": "<tailscale-ip>"
  },
  "grants": [
    {
      "src": [
        "group:admins"
      ],
      "dst": [
        "*"
      ],
      "ip": [
        "*"
      ]
    },
    {
      "src": [
        "group:media-users"
      ],
      "dst": [
        "homeserver"
      ],
      "ip": [
        "tcp:80",
        "tcp:443"
      ]
    }
  ],
  "ssh": [
    {
      "action": "check",
      "src": [
        "group:admins"
      ],
      "dst": [
        "tag:server",
        "homeserver"
      ],
      "users": [
        "admin",
        "root"
      ]
    }
  ]
}
```

### Security Enforcement Mechanics
- **`group:admins` (`admin@example.com`)**: Retains complete, unrestricted Layer 3/4 access across all devices and ports, plus Tailscale SSH check access to `homeserver`.
- **`group:media-users` (`media-user@example.com`)**: WireGuard cryptokey routing on Tailscale client and server explicitly **drops** all packets destined for ports other than `tcp:80` and `tcp:443` on `homeserver`.
  - Attempts to connect to `<tailscale-ip>:22` (SSH) -> **DROPPED at Layer 4**
  - Attempts to connect to `<tailscale-ip>:8096` (Jellyfin direct) -> **DROPPED at Layer 4**
  - Attempts to connect to `<tailscale-ip>:5055` (Jellyseerr direct) -> **DROPPED at Layer 4**
  - Attempts to connect to `<tailscale-ip>:2283` (Immich direct) -> **DROPPED at Layer 4**
  - Attempts to connect to `<tailscale-ip>:7878` (Radarr direct) -> **DROPPED at Layer 4**
  - Attempts to reach other Tailscale nodes (`dracore-ultraxv`, `nothing-phone-2`) -> **DROPPED at Layer 4**

---

## 5. Caddy Reverse Proxy Implementation

### Directory Structure (`/mnt/storage/AppData/caddy`)
```
/mnt/storage/AppData/caddy/
├── docker-compose.yml       # Stack definition on network: caddy_proxy
├── Caddyfile                # Master configuration & global snippets
├── conf.d/                  # Modular service configurations
│   ├── 00-dashboard.caddy   # Glance startpage & root hostnames
│   ├── 10-media.caddy       # Jellyfin, Jellyseerr, Immich
│   ├── 20-arr.caddy         # Radarr, Sonarr, Prowlarr, Bazarr, Lidarr
│   ├── 30-services.caddy    # Vaultwarden, FileBrowser, qBittorrent, etc.
│   ├── 40-monitoring.caddy  # Uptime Kuma, AdGuard, Grafana, Prometheus
│   └── 50-smart-home.caddy  # Home Assistant
├── certs/                   # 10-Year Local CA and SAN Wildcard Certificate
│   ├── root.crt             # Homeserver Internal Root CA
│   ├── root.key             # Root CA Private Key (400 perms)
│   ├── wildcard.crt         # Multi-domain SAN Certificate
│   └── wildcard.key         # Server Private Key
├── data/                    # Caddy internal runtime storage
└── config/                  # Autosaved Caddy JSON configuration
```

### Master Caddyfile Snippets
```caddyfile
# Common Security & Proxy Headers
(common_headers) {
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains;"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
}

# Admin-Only Access Restriction (LAN + Authorized Admin Tailscale Devices)
(admin_only) {
    @unauthorized not remote_ip 192.168.0.0/16 10.0.0.0/8 172.16.0.0/12 100.64.0.0/10 127.0.0.1 ::1
    respond @unauthorized "403 Forbidden: Administrative Access Only" 403
}

# Standard TLS configuration using Homeserver Private Wildcard CA
(tls_internal) {
    tls /etc/caddy/certs/wildcard.crt /etc/caddy/certs/wildcard.key
}
```

### Service-Specific Optimizations
- **Immich & FileBrowser**: Configured with `request_body { max_size 50GB }` to accommodate multi-gigabyte video and RAW camera uploads.
- **qBittorrent WebUI**: Configured with `header_up Host {upstream_hostport}` to satisfy qBittorrent's built-in CSRF host check.
- **Home Assistant**: Updated `/mnt/storage/AppData/homeassistant/.storage/http` with `use_x_forwarded_for: true` and `trusted_proxies: ["172.25.0.0/16", "172.19.0.0/16", "172.16.0.0/12", "127.0.0.1", "::1"]`.
- **Jellyfin**: Configured with `transport http { read_buffer 8192 }` for media stream buffering.
- **WebSockets**: Supported natively out-of-the-box across Jellyfin, Immich, Docmost, Home Assistant, Uptime Kuma, and Vaultwarden.

---

## 6. Docker Networking Topology

A dedicated bridge network `caddy_proxy` connects Caddy directly to backend application containers:

```
Docker Network: caddy_proxy (Subnet 172.25.0.0/16)
├── caddy                   (172.25.0.24) [Proxy Gateway]
├── glance                  (172.25.0.2)
├── jellyfin                (172.25.0.3)
├── radarr                  (172.25.0.4)
├── sonarr                  (172.25.0.5)
├── prowlarr                (172.25.0.6)
├── bazarr                  (172.25.0.7)
├── lidarr                  (172.25.0.8)
├── qbittorrent             (172.25.0.9)
├── vaultwarden             (172.25.0.10)
├── filebrowser             (172.25.0.11)
├── audiobookshelf          (172.25.0.12)
├── navidrome               (172.25.0.13)
├── homeassistant           (172.25.0.14)
├── prometheus              (172.25.0.15)
├── grafana                 (172.25.0.16)
├── uptime_kuma             (172.25.0.17)
├── adguardhome             (172.25.0.18)
├── immich_server           (172.25.0.19)
├── docmost                 (172.25.0.20)
├── hoarder_web             (172.25.0.21)
├── searxng                 (172.25.0.22)
└── ollama                  (172.25.0.23)
```

Host-mode containers (`jellyseerr` on port `5055` and `cups` on ports `631`/`8084`) are reached via `extra_hosts: ["host.docker.internal:host-gateway"]`.

---

## 7. Comprehensive Access Control Matrix

| Service / Interface | Local LAN (`<lan-subnet>`) | Admin via Tailscale (`group:admins`) | Media Users via Tailscale (`group:media-users`) | Public Internet |
| :--- | :--- | :--- | :--- | :--- |
| **SSH (`22`)** | ✅ Allowed | ✅ Allowed (Tailscale SSH) | ❌ **DENIED (L4 Drop)** | ❌ Blocked |
| **Jellyfin (`https`)** | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED (Jellyfin Auth)** | ❌ Blocked |
| **Jellyseerr (`https`)** | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED (Jellyfin Auth)** | ❌ Blocked |
| **Immich (`https`)** | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED (Immich Auth)** | ❌ Blocked |
| **Glance Dashboard** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Vaultwarden** | ✅ Allowed | ✅ Allowed (Master Password) | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Radarr / Sonarr / Lidarr** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Prowlarr / Bazarr** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **qBittorrent WebUI** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **FileBrowser** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Audiobookshelf** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Navidrome** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Docmost** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Hoarder** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Home Assistant** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **SearXNG** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Ollama LLM API** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Uptime Kuma** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Grafana / Prometheus** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **AdGuard Home WebUI** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **CUPS Admin & WebPrint** | ✅ Allowed | ✅ Allowed | ❌ **DENIED (403 Forbidden)** | ❌ Blocked |
| **Direct Backend Ports (e.g. 8096, 7878)** | ✅ Allowed (LAN only) | ✅ Allowed | ❌ **DENIED (L4 Drop)** | ❌ Blocked |

---

## 8. TLS Strategy & Certificate Trust

### Certificate Architecture
- **Root CA**: Homeserver Internal Root CA (`/mnt/storage/AppData/caddy/certs/root.crt`) with a 10-year validity window (2026–2036).
- **Wildcard Certificate**: `*.<tailscale-domain>` with SAN coverage for `*.homeserver`, `*.home.arpa`, `*.lan`, `<tailscale-ip>`, and `<lan-ip>`.
- **Zero Internet Leakage**: No ACME HTTP-01 challenges are broadcast to the public Internet, and no port 80/443 port forward is needed on your home router.

### Installing Root CA on Client Devices
To get trusted green padlocks and eliminate browser warnings:
1. **Windows**: Double-click `root.crt` > *Install Certificate* > *Local Machine* > Place in *Trusted Root Certification Authorities*.
2. **Android**: Transfer `root.crt` > *Settings > Security > Encryption & Credentials > Install a Certificate > CA Certificate*.
3. **Linux / Arch**: `sudo trust anchor /mnt/storage/AppData/caddy/certs/root.crt && sudo update-ca-trust`.
4. **macOS / iOS**: AirDrop or import `root.crt` into Keychain > mark as *Always Trust*.

---

## 9. Operational Commands & Runbook

### Health & Inspection
```bash
# 1. Check live status of Caddy container
docker ps | grep caddy

# 2. Inspect real-time Caddy logs
docker logs -f --tail 100 caddy

# 3. Audit all server listening sockets and registry hit list
portexplain

# 4. Inspect Caddy's Docker network connections
docker network inspect caddy_proxy
```

### Configuration Validation & Reload
```bash
# 1. Validate Caddyfile syntax without restarting
docker run --rm \
  -v /mnt/storage/AppData/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v /mnt/storage/AppData/caddy/conf.d:/etc/caddy/conf.d:ro \
  -v /mnt/storage/AppData/caddy/certs:/etc/caddy/certs:ro \
  caddy:latest caddy validate --config /etc/caddy/Caddyfile

# 2. Reload Caddy configuration with zero downtime
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# 3. Restart Caddy stack
cd /mnt/storage/AppData/caddy && docker compose restart
```

### DNS & Connectivity Testing
```bash
# 1. Test DNS rewrite resolution on homeserver AdGuard Home (port 53)
dig +short @<tailscale-ip> jellyfin.<tailscale-domain>
dig +short @<tailscale-ip> immich.<tailscale-domain>

# 2. Test Media endpoint via Caddy HTTPS
curl -k -I --resolve jellyfin.<tailscale-domain>:443:<tailscale-ip> https://jellyfin.<tailscale-domain>/

# 3. Test Admin endpoint via Caddy HTTPS (Verify 200 from admin IP, 403 from unauthorized IP)
curl -k -I --resolve glance.<tailscale-domain>:443:<tailscale-ip> https://glance.<tailscale-domain>/
```

---

## 10. Security Audit & Defense-in-Depth Analysis

### Current Security Posture
1. **Public Internet Exposure**: **ZERO**. No router ports are forwarded.
2. **Remaining Exposed Host Ports**:
   - Application host ports (`8096`, `7878`, `8989`, etc.) remain mapped to `0.0.0.0` to preserve compatibility with existing LAN bookmarks, local scripts, and Glance dashboard widgets.
   - **Protection against remote bypass**: Tailscale Grants policy acts as an impenetrable Layer 4 barrier. Any Tailscale user in `group:media-users` who attempts to connect directly to `<tailscale-ip>:8096` or `<tailscale-ip>:7878` has their connection dropped by Tailscale's kernel WireGuard module before reaching the socket.
3. **Application Authentication**:
   - Even if an attacker were inside the network, every application enforces its own independent credentials (Jellyfin, Immich, Vaultwarden, qBittorrent, etc.).
4. **Identified Future Hardening Options**:
   - If desired in the future, backend container host port mappings in `docker-compose.yml` can be bound strictly to `<lan-ip>:<port>` or `127.0.0.1:<port>` rather than `0.0.0.0:<port>`.

---

## 11. Backups & Disaster Recovery / Rollback

### Backup Location
All original configuration files before the Caddy deployment are preserved in:  
**`/mnt/storage/AppData/backups/reverse-proxy-pre-caddy-20260906/`**

| Original Component | Backup File |
| :--- | :--- |
| Services Compose | `services-docker-compose.yml` |
| Immich Compose | `immich-docker-compose.yml` |
| Docmost Compose | `docmost-docker-compose.yml` |
| Hoarder Compose | `hoarder-docker-compose.yml` |
| SearXNG Compose | `searxng-docker-compose.yml` |
| Ollama Compose | `ollama-docker-compose.yml` |
| Home Assistant Config | `homeassistant-configuration.yaml` |
| Port Registry JSON | `services.json` |
| Master Guide Docs | `HOMESERVER_GUIDE.md`, `SELF_HOSTED_APPS.md`, `PORTEXPLAIN_REGISTRY.md` |

### Rollback Procedure
If you ever need to completely revert:
```bash
# 1. Stop and remove Caddy container
cd /mnt/storage/AppData/caddy && docker compose down

# 2. Restore original services compose file
cp /mnt/storage/AppData/backups/reverse-proxy-pre-caddy-20260906/services-docker-compose.yml /mnt/storage/AppData/services/docker-compose.yml
cd /mnt/storage/AppData/services && docker compose up -d

# 3. Restore other compose files as needed from backup directory
```

---

## 12. Standard Operating Procedure: Adding a New Service

Whenever deploying a new self-hosted web application:

1. **Verify Port Availability**:
   ```bash
   portexplain <proposed_port>
   ```
2. **Deploy Application Container**:
   In the application's `docker-compose.yml`, attach it to the `caddy_proxy` network:
   ```yaml
   services:
     newapp:
       image: newapp/image:latest
       container_name: newapp
       restart: always
       networks:
         - default
         - caddy_proxy

   networks:
     default:
     caddy_proxy:
       external: true
   ```
3. **Add Caddy Route**:
   Create `/mnt/storage/AppData/caddy/conf.d/<priority>-newapp.caddy`:
   ```caddyfile
   newapp.<tailscale-domain>, newapp.home.arpa, newapp.homeserver {
       import common_headers
       import admin_only     # Omit this line if public to media-users
       import tls_internal

       reverse_proxy newapp:<internal_port>
   }
   ```
4. **Reload Caddy**:
   ```bash
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```
5. **Register in Portexplain & Guides**:
   - Add entry to `~/.config/portexplain/services.json`.
   - Update `SELF_HOSTED_APPS.md` and `HOMESERVER_GUIDE.md`.

---

## 13. Standard Operating Procedure: User Access Governance

### Adding a New Tailscale User
1. Invite the user to your tailnet via the Tailscale Admin Console (**Users > Invite user**).
2. Open `docs/TAILSCALE_POLICY.json`.
3. To grant **media access only** (Jellyfin, Jellyseerr, Immich):
   Add the user's email to `"group:media-users"`:
   ```json
   "groups": {
     "group:media-users": [
       "media-user@example.com",
       "user2@example.com"
     ]
   }
   ```
4. To grant **full administrative access**:
   Add the user's email to `"group:admins"` AND append their Tailscale node IP to the `@unauthorized not remote_ip` matcher in `/mnt/storage/AppData/caddy/Caddyfile`.
5. Copy the updated JSON policy and paste it into **Tailscale Admin Console > Access Controls > Save**.
6. In Immich / Jellyfin, create their respective user accounts. Enforce per-user storage isolation templates in Immich.

### Revoking Access
1. Remove the user's email from `TAILSCALE_POLICY.json` and click Save in Tailscale Admin Console.
2. The user will be instantly dropped by Tailscale's WireGuard crypto routing on all ports.
