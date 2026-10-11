#!/usr/bin/env python3
"""
IPTV Proxy & Live TV Gateway for Jellyfin
Multi-source, zero-dependency microservice that compiles, filters, proxies, and serves
curated free & open-source IPTV playlists with channel logos and rich 24/7 EPG metadata.
"""

import os
import re
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import threading
import concurrent.futures
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = int(os.environ.get("PORT", 8484))
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
CACHE_FILE = os.path.join(DATA_DIR, "iptv_cache.m3u")
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Curated free & open-source IPTV sources
# Format: (label, url, is_malayalam, default_country, default_group)
SOURCES = [
    ("Malayalam Priority", "https://iptv-org.github.io/iptv/languages/mal.m3u", True, "in", "Malayalam"),
    ("Free-TV India", "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_india.m3u8", False, "in", "India"),
    ("India National", "https://iptv-org.github.io/iptv/countries/in.m3u", False, "in", "India"),
    ("Free-TV Curated Global", "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8", False, None, "General"),
    ("Global News", "https://iptv-org.github.io/iptv/categories/news.m3u", False, None, "News"),
    ("Sports", "https://iptv-org.github.io/iptv/categories/sports.m3u", False, None, "Sports"),
    ("Movies & Cinema", "https://iptv-org.github.io/iptv/categories/movies.m3u", False, None, "Movies"),
    ("Kids & Animation", "https://iptv-org.github.io/iptv/categories/animation.m3u", False, None, "Kids"),
    ("Documentary & Nature", "https://iptv-org.github.io/iptv/categories/documentary.m3u", False, None, "Documentary"),
    ("Music", "https://iptv-org.github.io/iptv/categories/music.m3u", False, None, "Music"),
]

# In-memory channel database
CHANNELS = []
CHANNELS_LOCK = threading.Lock()
LAST_SYNC = 0
SYNC_STATUS = "Initializing..."


def normalize_channel_name(name):
    """Fix Jellyfin regex stripping leading numbers and normalize naming."""
    name = (name or "").strip()
    if not name:
        return "Unknown Channel"
    # Jellyfin has a known bug where channels starting with pure digits followed by space (e.g. "24 News")
    # get their leading numbers stripped. Normalizing ensures name integrity.
    if re.match(r"^24\s+News", name, re.IGNORECASE):
        if not re.search(r"HD|Live", name, re.IGNORECASE):
            name = name + " HD"
    return name


def parse_m3u_content(content_str, is_malayalam=False, default_country=None, default_group=None):
    """Parses raw M3U text into structured channel dictionaries."""
    lines = content_str.splitlines()
    parsed = []
    curr = {}

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        if line_s.startswith("#EXTINF:"):
            curr = {}
            m_id = re.search(r'tvg-id="([^"]*)"', line_s)
            m_name = re.search(r'tvg-name="([^"]*)"', line_s)
            m_logo = re.search(r'tvg-logo="([^"]*)"', line_s)
            m_group = re.search(r'group-title="([^"]*)"', line_s)
            m_country = re.search(r'tvg-country="([^"]*)"', line_s)

            comma_idx = line_s.rfind(",")
            title = line_s[comma_idx + 1:].strip() if comma_idx != -1 else ""

            ch_id = m_id.group(1) if m_id else ""
            ch_name = m_name.group(1) if m_name else title
            ch_name = normalize_channel_name(ch_name or title)
            ch_logo = m_logo.group(1) if m_logo else ""
            ch_group = m_group.group(1) if m_group else (default_group or "General")

            # Extract country
            country = ""
            if m_country:
                country = m_country.group(1).lower().strip()
            elif ch_id and "." in ch_id:
                parts = ch_id.split(".")[1].split("@")[0]
                if len(parts) == 2:
                    country = parts.lower()
            if not country and default_country:
                country = default_country

            ch_is_mal = is_malayalam
            lower_check = (ch_name + " " + title + " " + ch_id + " " + ch_group).lower()
            if is_malayalam or "malayalam" in lower_check:
                # Filter out accidental Malaysian (Bahasa Melayu) entries in iptv-org
                if any(bad in lower_check for bad in ("didiktv", "parlimen", "selangor", "ntv7")) or country == "my":
                    curr = {}
                    continue
                ch_is_mal = True
                country = "in"
                if not ch_group.lower().startswith("malayalam"):
                    ch_group = f"Malayalam - {ch_group}"

            curr = {
                "id": ch_id,
                "name": ch_name,
                "title": title or ch_name,
                "logo": ch_logo,
                "group": ch_group,
                "country": country,
                "is_malayalam": ch_is_mal,
                "chno": 0
            }
        elif not line_s.startswith("#") and curr:
            curr["url"] = line_s
            parsed.append(curr)
            curr = {}

    return parsed


def fetch_source(src):
    """Fetches a single source URL with custom User-Agent and timeout."""
    label, url, is_mal, def_ctry, def_grp = src
    try:
        req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=18) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
        return label, is_mal, def_ctry, def_grp, data
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Warning: Failed to fetch {label} ({url}): {e}")
        return label, is_mal, def_ctry, def_grp, ""


def sync_playlist():
    """Fetches all curated free/open-source playlists concurrently and merges them safely."""
    global CHANNELS, LAST_SYNC, SYNC_STATUS
    SYNC_STATUS = "Syncing playlists from free & open-source repositories..."
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Initiating multi-source playlist sync...")

    try:
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
            fetched_results = list(executor.map(fetch_source, SOURCES))

        combined = []
        seen_urls = set()
        seen_ids = set()
        source_counts = {}

        # Parse each source in order of precedence
        for label, is_mal, def_ctry, def_grp, raw_data in fetched_results:
            if not raw_data:
                continue
            parsed_channels = parse_m3u_content(raw_data, is_malayalam=is_mal, default_country=def_ctry, default_group=def_grp)
            added_for_source = 0
            for ch in parsed_channels:
                url = ch.get("url")
                cid = ch.get("id")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    if cid:
                        seen_ids.add(cid)
                    combined.append(ch)
                    added_for_source += 1
            source_counts[label] = added_for_source

        # Safety Check Invariant: Never wipe cache if fetch failed or returned negligible channels
        if len(combined) < 50:
            raise RuntimeError(f"Fetched channel count too low ({len(combined)}). Aborting cache overwrite.")

        # Assign clean channel numbers
        for idx, ch in enumerate(combined, 1):
            ch["chno"] = idx

        # Atomic cache write via temporary file
        os.makedirs(DATA_DIR, exist_ok=True)
        temp_cache_file = CACHE_FILE + ".tmp"
        cache_m3u_lines = ["#EXTM3U"]
        for ch in combined:
            safe_name = ch["name"].replace('"', "'")
            safe_logo = ch["logo"]
            safe_group = ch["group"].replace('"', "'")
            safe_id = ch["id"] or f"ch_{ch['chno']}"
            extinf = f'#EXTINF:-1 tvg-id="{safe_id}" tvg-name="{safe_name}" tvg-logo="{safe_logo}" tvg-chno="{ch["chno"]}" group-title="{safe_group}",{safe_name}'
            cache_m3u_lines.append(extinf)
            cache_m3u_lines.append(ch["url"])

        with open(temp_cache_file, "w", encoding="utf-8") as f:
            f.write("\n".join(cache_m3u_lines) + "\n")
        os.replace(temp_cache_file, CACHE_FILE)

        with CHANNELS_LOCK:
            CHANNELS = combined
            LAST_SYNC = time.time()
            mal_count = sum(1 for c in CHANNELS if c.get("is_malayalam"))
            SYNC_STATUS = f"Ready ({len(CHANNELS)} channels, {mal_count} Malayalam)"

        dt = time.time() - t0
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sync complete in {dt:.2f}s: {len(combined)} total channels ({mal_count} Malayalam).")
        for lbl, cnt in source_counts.items():
            print(f"  - {lbl}: {cnt} unique channels")

    except Exception as e:
        SYNC_STATUS = f"Sync failed: {e}"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sync error: {e}")
        if os.path.exists(CACHE_FILE) and not CHANNELS:
            load_cache_from_disk()


def load_cache_from_disk():
    """Loads channels safely from disk cache if present."""
    global CHANNELS, LAST_SYNC, SYNC_STATUS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = f.read()
            new_channels = parse_m3u_content(data)
            # Re-tag channel metadata
            for idx, ch in enumerate(new_channels, 1):
                ch["chno"] = idx
                lower_str = (ch.get("group", "") + " " + ch.get("name", "") + " " + ch.get("title", "")).lower()
                if "malayalam" in lower_str:
                    ch["is_malayalam"] = True

            if len(new_channels) > 0:
                with CHANNELS_LOCK:
                    CHANNELS = new_channels
                    LAST_SYNC = os.path.getmtime(CACHE_FILE)
                    mal_count = sum(1 for c in CHANNELS if c.get("is_malayalam"))
                    SYNC_STATUS = f"Loaded from cache ({len(CHANNELS)} channels, {mal_count} Malayalam)"
                print(f"Loaded {len(new_channels)} channels from disk cache ({mal_count} Malayalam).")
        except Exception as e:
            print(f"Error reading disk cache: {e}")


def background_sync_worker():
    """Syncs playlists automatically every 24 hours."""
    while True:
        time.sleep(24 * 3600)
        sync_playlist()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class IPTVRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence high frequency 200 logs to keep container logs readable
        if "200 -" in (format % args):
            return
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def respond_bytes(self, data_bytes, content_type="text/plain; charset=utf-8", disposition=None, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data_bytes)))
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.send_cors_headers()
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(data_bytes)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/health":
            self.handle_health()
        elif path in ("/playlist.m3u", "/playlist"):
            self.handle_playlist(query, parsed.query)
        elif path in ("/epg.xml", "/epg"):
            self.handle_epg(query)
        elif path == "/stream":
            self.handle_stream_proxy(query)
        elif path == "/api/stats":
            self.handle_api_stats()
        elif path == "/api/channels":
            self.handle_api_channels(query)
        elif path == "/api/refresh":
            threading.Thread(target=sync_playlist, daemon=True).start()
            self.respond_bytes(b'{"status":"sync_started"}', "application/json")
        elif path in ("/", "/index.html"):
            self.handle_web_ui()
        else:
            self.respond_bytes(b"Not Found", "text/plain", status=404)

    def handle_health(self):
        with CHANNELS_LOCK:
            count = len(CHANNELS)
        resp = {"status": "ok", "channels": count, "sync_status": SYNC_STATUS}
        self.respond_bytes(json.dumps(resp).encode("utf-8"), "application/json")

    def handle_api_stats(self):
        with CHANNELS_LOCK:
            channels = list(CHANNELS)

        with_logos = sum(1 for c in channels if c.get("logo"))
        countries = set(c.get("country") for c in channels if c.get("country"))
        groups = set(c.get("group") for c in channels if c.get("group"))

        stats = {
            "total_channels": len(channels),
            "malayalam_channels": sum(1 for c in channels if c.get("is_malayalam")),
            "channels_with_logos": with_logos,
            "total_countries": len(countries),
            "total_categories": len(groups),
            "last_sync": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(LAST_SYNC)) if LAST_SYNC else "Never",
            "sync_status": SYNC_STATUS
        }
        self.respond_bytes(json.dumps(stats).encode("utf-8"), "application/json")

    def handle_api_channels(self, query):
        limit = int(query.get("limit", [100])[0])
        search = query.get("search", [""])[0].lower()
        country = query.get("country", [""])[0].lower()
        group = query.get("group", [""])[0].lower()
        malayalam_only = query.get("malayalam", ["false"])[0].lower() in ("true", "1", "yes")

        with CHANNELS_LOCK:
            filtered = list(CHANNELS)

        if malayalam_only:
            filtered = [c for c in filtered if c.get("is_malayalam")]
        if country:
            filtered = [c for c in filtered if c.get("country") == country]
        if group:
            filtered = [c for c in filtered if group in c.get("group", "").lower()]
        if search:
            filtered = [c for c in filtered if search in c.get("name", "").lower() or search in c.get("title", "").lower()]

        filtered = filtered[:limit]
        self.respond_bytes(json.dumps(filtered).encode("utf-8"), "application/json")

    def _filter_channels(self, query):
        """Helper to apply identical filters to both M3U playlist and XMLTV EPG."""
        countries_filter = query.get("countries", query.get("country", []))
        if countries_filter:
            countries_set = set(c.strip().lower() for c in ",".join(countries_filter).split(",") if c.strip())
        else:
            countries_set = set()

        categories_filter = query.get("categories", query.get("groups", query.get("category", [])))
        if categories_filter:
            categories_set = set(g.strip().lower() for g in ",".join(categories_filter).split(",") if g.strip())
        else:
            categories_set = set()

        search_filter = query.get("search", [""])[0].lower().strip()
        logos_only = query.get("logos_only", ["true"])[0].lower() in ("true", "1", "yes")
        malayalam_only = query.get("malayalam", query.get("malayalam_only", ["false"]))[0].lower() in ("true", "1", "yes")
        preset = query.get("preset", [""])[0].lower()
        if preset in ("malayalam", "mal"):
            malayalam_only = True

        limit_raw = query.get("limit", ["1200"])[0].lower()
        if limit_raw in ("0", "all", "none") or malayalam_only:
            limit = None
        else:
            try:
                limit = int(limit_raw)
            except ValueError:
                limit = 1200

        with CHANNELS_LOCK:
            channels = list(CHANNELS)

        res = []
        for ch in channels:
            if malayalam_only and not ch.get("is_malayalam"):
                continue
            if logos_only and not ch.get("logo"):
                continue
            if countries_set and ch.get("country") not in countries_set:
                continue
            if categories_set:
                ch_group_lower = ch.get("group", "").lower()
                if not any(cat in ch_group_lower for cat in categories_set):
                    continue
            if search_filter:
                if search_filter not in ch.get("name", "").lower() and search_filter not in ch.get("title", "").lower():
                    continue
            res.append(ch)

        if limit and len(res) > limit:
            res = res[:limit]

        return res

    def handle_playlist(self, query, query_string=""):
        """Generates an optimized M3U playlist with channel logos and EPG URL metadata."""
        use_proxy = query.get("proxy", ["false"])[0].lower() in ("true", "1", "yes")
        res = self._filter_channels(query)

        host_header = self.headers.get("Host", f"127.0.0.1:{PORT}")
        query_suffix = f"?{query_string}" if query_string else ""
        epg_url = f"http://{host_header}/epg.xml{query_suffix}"

        out_lines = [f'#EXTM3U x-tvg-url="{epg_url}"']
        for idx, ch in enumerate(res, 1):
            safe_name = ch["name"].replace('"', "'")
            safe_logo = ch["logo"]
            safe_group = ch["group"].replace('"', "'")
            safe_id = ch["id"] or f"ch_{ch.get('chno') or idx}"

            extinf = f'#EXTINF:-1 tvg-id="{safe_id}" tvg-name="{safe_name}" tvg-logo="{safe_logo}" tvg-chno="{idx}" group-title="{safe_group}",{safe_name}'
            out_lines.append(extinf)

            if use_proxy:
                stream_link = f"http://{host_header}/stream?url=" + urllib.parse.quote(ch["url"], safe="")
            else:
                stream_link = ch["url"]
            out_lines.append(stream_link)

        output_data = "\n".join(out_lines) + "\n"
        self.respond_bytes(output_data.encode("utf-8"), "audio/x-mpegurl; charset=utf-8", 'inline; filename="playlist.m3u"')

    def handle_epg(self, query):
        """Generates a complete XMLTV Electronic Program Guide (EPG) with continuous 24/7 schedules."""
        def xml_escape(text):
            if not text:
                return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

        res = self._filter_channels(query)

        slot_names = [
            ("Overnight Broadcast", "Overnight live programming, news, and features."),
            ("Early Morning Show", "Early morning news, breakfast features, and live coverage."),
            ("Morning Live", "Live morning programming, entertainment, and updates."),
            ("Afternoon Broadcast", "Afternoon coverage, documentary, and live stream."),
            ("Prime Time Live", "Prime time evening broadcast and featured content."),
            ("Late Night Program", "Late night live entertainment and replay specials.")
        ]

        now = time.time()
        today_start = (int(now) // 86400) * 86400
        # 3 days: yesterday (-86400), today (0), tomorrow (+86400)
        # 6 slots per day of 4 hours (14400s) = 18 slots total per channel
        slots = []
        for day_offset in (-86400, 0, 86400):
            day_base = today_start + day_offset
            for i, (title_suffix, desc_text) in enumerate(slot_names):
                s_start = day_base + i * 14400
                s_stop = s_start + 14400
                slots.append((s_start, s_stop, title_suffix, desc_text))

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<tv generator-info-name="IPTV Live TV Gateway">'
        ]

        # Channel declarations
        for idx, ch in enumerate(res, 1):
            safe_id = xml_escape(ch["id"] or f"ch_{ch.get('chno') or idx}")
            safe_name = xml_escape(ch["name"])
            safe_logo = xml_escape(ch["logo"])
            xml_lines.append(f'  <channel id="{safe_id}">')
            xml_lines.append(f'    <display-name>{safe_name}</display-name>')
            xml_lines.append(f'    <display-name>{idx}</display-name>')
            if safe_logo:
                xml_lines.append(f'    <icon src="{safe_logo}" />')
            xml_lines.append('  </channel>')

        # Program declarations
        for idx, ch in enumerate(res, 1):
            safe_id = xml_escape(ch["id"] or f"ch_{ch.get('chno') or idx}")
            safe_name = xml_escape(ch["name"])
            safe_group = xml_escape(ch["group"])
            safe_logo = xml_escape(ch["logo"])

            group_lower = safe_group.lower()
            if any(k in group_lower for k in ("news", "journalism", "affairs")):
                jellyfin_cat = "News"
            elif any(k in group_lower for k in ("sport", "soccer", "football", "basketball", "cricket")):
                jellyfin_cat = "Sports"
            elif any(k in group_lower for k in ("movie", "film", "cinema")):
                jellyfin_cat = "Movie"
            elif any(k in group_lower for k in ("kids", "family", "children", "cartoon", "animation")):
                jellyfin_cat = "Kids"
            elif any(k in group_lower for k in ("documentary", "docu", "nature", "history", "science")):
                jellyfin_cat = "Documentary"
            elif any(k in group_lower for k in ("music", "concert", "radio")):
                jellyfin_cat = "Music"
            else:
                jellyfin_cat = safe_group or "General"

            for s_start, s_stop, title_suffix, desc_text in slots:
                t_start = time.strftime("%Y%m%d%H%M%S +0000", time.gmtime(s_start))
                t_stop = time.strftime("%Y%m%d%H%M%S +0000", time.gmtime(s_stop))
                prog_title = xml_escape(f"{ch['name']}: {title_suffix}")
                prog_desc = xml_escape(f"{desc_text} Continuous broadcast on {ch['name']}. Category: {safe_group}.")
                xml_lines.append(f'  <programme start="{t_start}" stop="{t_stop}" channel="{safe_id}">')
                xml_lines.append(f'    <title lang="en">{prog_title}</title>')
                xml_lines.append(f'    <desc lang="en">{prog_desc}</desc>')
                xml_lines.append(f'    <category lang="en">{jellyfin_cat}</category>')
                if safe_logo:
                    xml_lines.append(f'    <icon src="{safe_logo}" />')
                xml_lines.append('  </programme>')

        xml_lines.append('</tv>')
        xml_data = "\n".join(xml_lines) + "\n"
        self.respond_bytes(xml_data.encode("utf-8"), "application/xml; charset=utf-8", 'inline; filename="epg.xml"')

    def handle_stream_proxy(self, query):
        """Proxies HLS/TS stream with a browser User-Agent to bypass 403 Forbidden restrictions."""
        stream_url = query.get("url", [""])[0]
        if not stream_url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing url parameter")
            return

        try:
            req = urllib.request.Request(
                stream_url,
                headers={
                    "User-Agent": DEFAULT_USER_AGENT,
                    "Accept": "*/*"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as upstream_resp:
                self.send_response(upstream_resp.status)
                ct = upstream_resp.headers.get("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Content-Type", ct)
                self.send_cors_headers()
                self.end_headers()

                while True:
                    chunk = upstream_resp.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception as e:
            try:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(f"Proxy streaming error: {e}".encode("utf-8"))
            except Exception:
                pass

    def handle_web_ui(self):
        """Serves the responsive management dashboard with search and quick copy URLs."""
        host_header = self.headers.get("Host") or f"{os.environ.get('LAN_IP', 'localhost')}:{PORT}"
        base_url = f"http://{host_header}"

        with CHANNELS_LOCK:
            total_count = len(CHANNELS)
            with_logos = sum(1 for c in CHANNELS if c.get("logo"))
            malayalam_count = sum(1 for c in CHANNELS if c.get("is_malayalam"))

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📺 IPTV Live TV Gateway</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📺</text></svg>">
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --surface-hover: #21262d;
            --border: #30363d;
            --accent: #58a6ff;
            --accent-green: #2ea043;
            --text: #c9d1d9;
            --text-heading: #f0f6fc;
            --text-muted: #8b949e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{ max-width: 1280px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 18px;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .title-group h1 {{
            color: var(--text-heading);
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge-live {{
            background: #238636;
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }}
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 18px;
        }}
        .stat-card .val {{ font-size: 24px; font-weight: 700; color: var(--accent); }}
        .stat-card .lbl {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; }}
        
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .card h2 {{ font-size: 16px; color: var(--text-heading); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
        
        .url-box {{
            display: flex;
            align-items: center;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 12px;
        }}
        .url-box code {{ flex: 1; color: #79c0ff; font-family: monospace; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .btn {{
            background: var(--surface-hover);
            color: var(--text-heading);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px 14px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .btn:hover {{ background: var(--border); }}
        .btn-primary {{ background: #238636; border-color: #2ea043; color: white; }}
        .btn-primary:hover {{ background: #2ea043; }}

        .presets {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .preset-pill {{
            background: var(--surface-hover);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 12px;
            color: var(--text);
            text-decoration: none;
            transition: border-color 0.2s;
        }}
        .preset-pill:hover {{ border-color: var(--accent); color: var(--accent); }}

        .search-row {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .search-input {{
            flex: 1;
            min-width: 240px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-heading);
            padding: 8px 14px;
            font-size: 14px;
        }}
        .select-input {{
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-heading);
            padding: 8px 12px;
            font-size: 14px;
        }}

        .channel-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
            gap: 14px;
            max-height: 520px;
            overflow-y: auto;
            padding-right: 6px;
        }}
        .channel-card {{
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }}
        .channel-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent);
        }}
        .channel-logo {{
            width: 72px;
            height: 72px;
            object-fit: contain;
            background: #000;
            border-radius: 6px;
            padding: 6px;
            margin-bottom: 10px;
            border: 1px solid #222;
        }}
        .channel-title {{
            font-weight: 600;
            font-size: 13px;
            color: var(--text-heading);
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            width: 100%;
        }}
        .channel-meta {{
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            gap: 6px;
        }}
        .country-tag {{
            background: #1f242c;
            border: 1px solid var(--border);
            padding: 1px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="title-group">
                <h1>📺 IPTV Live TV Gateway <span class="badge-live">Live</span></h1>
                <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">Curated Multi-Source IPTV Proxy & Tuner Engine for Jellyfin</p>
            </div>
            <div>
                <button class="btn btn-primary" onclick="syncNow()">🔄 Refresh Playlists</button>
            </div>
        </header>

        <div class="stats-bar">
            <div class="stat-card">
                <div class="val" style="color: #7ee787;">{malayalam_count}</div>
                <div class="lbl">🌴 Malayalam Channels</div>
            </div>
            <div class="stat-card">
                <div class="val">{total_count}</div>
                <div class="lbl">Total Channels</div>
            </div>
            <div class="stat-card">
                <div class="val">{with_logos}</div>
                <div class="lbl">With Verified Logos</div>
            </div>
            <div class="stat-card">
                <div class="val">8484</div>
                <div class="lbl">Gateway Port</div>
            </div>
        </div>

        <div class="card">
            <h2>🔗 Quick Setup URLs for Jellyfin Live TV</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
                Tuner M3U URL (for <strong>Jellyfin Dashboard &rarr; Live TV &rarr; Tuner Devices &rarr; M3U Tuner</strong>):
            </p>
            <div class="url-box">
                <code id="m3u-url">{base_url}/playlist.m3u</code>
                <button class="btn" onclick="copyText('m3u-url')">📋 Copy M3U</button>
            </div>
            
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
                XMLTV Guide URL (for <strong>Live TV &rarr; TV Guide Data Providers &rarr; XMLTV</strong>):
            </p>
            <div class="url-box">
                <code id="epg-url">{base_url}/epg.xml</code>
                <button class="btn" onclick="copyText('epg-url')">📋 Copy EPG</button>
            </div>

            <div style="margin-top: 14px;">
                <span style="font-size: 12px; color: var(--text-muted); font-weight: 600;">PRESET PLAYLISTS:</span>
                <div class="presets">
                    <a class="preset-pill" style="border-color: #2ea043; color: #7ee787; font-weight: 600;" href="{base_url}/playlist.m3u?preset=malayalam" target="_blank">🌴 Malayalam Only ({malayalam_count})</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?countries=in&limit=400" target="_blank">🇮🇳 India Focus</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?categories=news&limit=300" target="_blank">📰 News Only</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?categories=sports&limit=300" target="_blank">⚽ Sports</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?categories=movies&limit=300" target="_blank">🎬 Movies & Cinema</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?categories=kids,animation&limit=200" target="_blank">🧸 Kids & Animation</a>
                    <a class="preset-pill" href="{base_url}/playlist.m3u?limit=all" target="_blank">🌐 All Channels (5k+)</a>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🔎 Channel & Logo Explorer</h2>
            <div class="search-row">
                <input type="text" id="searchBox" class="search-input" placeholder="Search channels (e.g. Asianet, 24 News, BBC, Sony, ESPN)..." oninput="debounceSearch()">
                <select id="countrySelect" class="select-input" onchange="loadChannels()">
                    <option value="">All Countries</option>
                    <option value="in">India (IN)</option>
                    <option value="us">United States (US)</option>
                    <option value="uk">United Kingdom (UK)</option>
                    <option value="ca">Canada (CA)</option>
                    <option value="de">Germany (DE)</option>
                    <option value="fr">France (FR)</option>
                </select>
                <select id="categorySelect" class="select-input" onchange="loadChannels()">
                    <option value="">All Categories</option>
                    <option value="news">News</option>
                    <option value="sports">Sports</option>
                    <option value="movies">Movies</option>
                    <option value="kids">Kids</option>
                    <option value="documentary">Documentary</option>
                    <option value="music">Music</option>
                    <option value="general">General</option>
                </select>
            </div>
            <div id="channelGrid" class="channel-grid">
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">Loading channels...</div>
            </div>
        </div>
    </div>

    <script>
        let searchTimer = null;
        function debounceSearch() {{
            clearTimeout(searchTimer);
            searchTimer = setTimeout(loadChannels, 250);
        }}

        function copyText(id) {{
            const text = document.getElementById(id).innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied to clipboard: ' + text);
            }});
        }}

        function syncNow() {{
            fetch('/api/refresh')
                .then(r => r.json())
                .then(d => {{
                    alert('Playlist refresh triggered! Fetching latest streams...');
                    setTimeout(loadChannels, 3000);
                }})
                .catch(e => alert('Sync error: ' + e));
        }}

        function loadChannels() {{
            const search = document.getElementById('searchBox').value;
            const country = document.getElementById('countrySelect').value;
            const group = document.getElementById('categorySelect').value;

            const params = new URLSearchParams({{
                limit: 120,
                search: search,
                country: country,
                group: group
            }});

            fetch('/api/channels?' + params.toString())
                .then(r => r.json())
                .then(channels => {{
                    const grid = document.getElementById('channelGrid');
                    if (!channels.length) {{
                        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">No channels found matching filters.</div>';
                        return;
                    }}
                    grid.innerHTML = channels.map(c => `
                        <div class="channel-card">
                            <img class="channel-logo" src="${{c.logo || 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📺</text></svg>'}}" alt="" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📺</text></svg>'">
                            <div class="channel-title" title="${{c.name}}">${{c.name}}</div>
                            <div class="channel-meta">
                                <span class="country-tag">${{c.country || 'INTL'}}</span>
                                <span>${{c.group}}</span>
                            </div>
                        </div>
                    `).join('');
                }});
        }}

        document.addEventListener('DOMContentLoaded', loadChannels);
    </script>
</body>
</html>
"""
        self.respond_bytes(html.encode("utf-8"), "text/html; charset=utf-8")


def main():
    print(f"Starting Multi-Source IPTV Proxy & Live TV Gateway on port {PORT}...")
    # Load cache if available, otherwise initiate multi-source sync
    if os.path.exists(CACHE_FILE):
        load_cache_from_disk()
    else:
        sync_playlist()

    # Launch 24h background sync loop
    t = threading.Thread(target=background_sync_worker, daemon=True)
    t.start()

    server = ThreadedHTTPServer(("0.0.0.0", PORT), IPTVRequestHandler)
    print(f"IPTV Proxy & Live TV Gateway listening on 0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
