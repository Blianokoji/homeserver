#!/usr/bin/env python3
"""
portexplain - Homeserver Port & Self-Hosted Software Intelligence Tool
Explains what ports are running what software, displays a comprehensive Hit List
of homeserver self-hosted applications, and audits active network sockets.
"""

from signal import signal, SIGPIPE, SIG_DFL
try:
    signal(SIGPIPE, SIG_DFL)
except Exception:
    pass
import os
import sys
import json
import socket
import subprocess
import shutil
import argparse
import re
from typing import Dict, List, Any, Optional, Tuple

REGISTRY_PATH = os.path.expanduser("~/.config/portexplain/services.json")
DOC_REGISTRY_PATH = os.path.expanduser("~/PORTEXPLAIN_REGISTRY.md")
DOC_APPS_PATH = os.path.expanduser("~/SELF_HOSTED_APPS.md")
DOC_GUIDE_PATH = os.path.expanduser("~/HOMESERVER_GUIDE.md")

# Default metadata fallback
DEFAULT_METADATA = {
    "hostname": "homeserver",
    "lan_ip": "127.0.0.1",
    "tailscale_ip": "N/A",
    "tailscale_fqdn": "homeserver.local",
    "storage_root": "/mnt/storage"
}

def detect_lan_ip() -> str:
    """Dynamically determine the host's primary LAN IPv4 address."""
    if os.environ.get("LAN_IP"):
        return os.environ["LAN_IP"]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except Exception:
        pass
    try:
        out = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"src\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"

def detect_tailscale_info() -> Tuple[Optional[str], Optional[str]]:
    """Dynamically discover Tailscale IPv4 and Tailscale FQDN."""
    env_ts_ip = os.environ.get("TAILSCALE_IP")
    env_ts_fqdn = os.environ.get("TAILSCALE_FQDN")
    ts_ip = env_ts_ip
    ts_fqdn = env_ts_fqdn

    if shutil.which("tailscale"):
        if not ts_ip:
            try:
                out = subprocess.check_output(["tailscale", "ip", "-4"], text=True, stderr=subprocess.DEVNULL).strip()
                if out:
                    ts_ip = out.splitlines()[0].strip()
            except Exception:
                pass
        if not ts_fqdn:
            try:
                out = subprocess.check_output(["tailscale", "status", "--json"], text=True, stderr=subprocess.DEVNULL)
                status = json.loads(out)
                dns_name = status.get("Self", {}).get("DNSName", "").rstrip(".")
                if dns_name:
                    ts_fqdn = dns_name
            except Exception:
                pass
    return ts_ip, ts_fqdn

def resolve_server_metadata(raw_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge detected server metadata with configured registry overrides and environment variables."""
    raw = raw_meta or {}
    detected_lan = detect_lan_ip()
    detected_ts_ip, detected_ts_fqdn = detect_tailscale_info()

    hostname = os.environ.get("SERVER_HOSTNAME") or raw.get("hostname") or socket.gethostname() or "homeserver"
    lan_ip = os.environ.get("LAN_IP") or raw.get("lan_ip") or detected_lan
    ts_ip = os.environ.get("TAILSCALE_IP") or detected_ts_ip or raw.get("tailscale_ip") or "N/A"
    ts_fqdn = os.environ.get("TAILSCALE_FQDN") or detected_ts_fqdn or raw.get("tailscale_fqdn") or f"{hostname}.local"
    storage_root = os.environ.get("STORAGE_ROOT") or raw.get("storage_root") or "/mnt/storage"

    return {
        "hostname": hostname,
        "lan_ip": lan_ip,
        "tailscale_ip": ts_ip,
        "tailscale_fqdn": ts_fqdn,
        "storage_root": storage_root
    }

# ANSI Color codes
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

def supports_color() -> bool:
    """Check if stdout supports ANSI color output."""
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return True

USE_COLOR = supports_color()
ANSI_REGEX = re.compile(r"\x1b\[[0-9;]*m")

def c(text: str, color_code: str) -> str:
    """Wrap text in ANSI color if supported."""
    if not USE_COLOR:
        return str(text)
    return f"{color_code}{text}{Color.RESET}"

def visible_len(text: str) -> int:
    """Calculate visible character length excluding ANSI color escape sequences."""
    return len(ANSI_REGEX.sub("", str(text)))

def pad_ansi(text: str, width: int, align: str = "left") -> str:
    """Pad a string to exact visible width accounting for ANSI color codes."""
    v_len = visible_len(text)
    diff = max(0, width - v_len)
    if align == "left":
        return str(text) + (" " * diff)
    elif align == "right":
        return (" " * diff) + str(text)
    else:
        left_pad = diff // 2
        right_pad = diff - left_pad
        return (" " * left_pad) + str(text) + (" " * right_pad)

def get_terminal_width() -> int:
    try:
        return shutil.get_terminal_size((140, 24)).columns
    except Exception:
        return 140

def load_registry() -> Dict[str, Any]:
    """Load services.json registry or return defaults."""
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"Warning: Could not read {REGISTRY_PATH}: {e}\n")

    # Search fallback bundled paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(script_dir, "services.json"),
        os.path.join(script_dir, "..", "services.json"),
        os.path.join(script_dir, "portexplain", "services.json"),
        os.path.join(script_dir, "..", "portexplain", "services.json"),
        "/usr/local/share/portexplain/services.json",
        "/etc/portexplain/services.json",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                try:
                    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
                    with open(REGISTRY_PATH, "w", encoding="utf-8") as f_out:
                        json.dump(data, f_out, indent=2)
                except Exception:
                    pass
                return data
            except Exception:
                pass

    return {"server_metadata": DEFAULT_METADATA, "selfhosted_services": [], "known_system_ports": {}}

def get_docker_containers() -> Dict[str, Dict[str, Any]]:
    """Query Docker daemon for all running/stopped containers."""
    containers = {}
    try:
        cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True)
        for line in res.stdout.strip().splitlines():
            if not line:
                continue
            try:
                data = json.loads(line)
                name = data.get("Names", "")
                containers[name] = data
            except Exception:
                pass
    except Exception:
        pass
    return containers

def get_systemd_status(unit: str, user: bool = False) -> Tuple[bool, str]:
    """Check if a systemd service is active."""
    try:
        cmd = ["systemctl"]
        if user:
            cmd.append("--user")
        cmd.extend(["is-active", unit])
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        status = res.stdout.strip()
        return (status == "active", status)
    except Exception:
        return (False, "unknown")

def get_active_sockets() -> List[Dict[str, Any]]:
    """Query ss tool for all listening TCP and UDP sockets with process info."""
    sockets = []
    try:
        cmd = ["ss", "-tulnpe"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        lines = res.stdout.strip().splitlines()
        
        # Also run ss -tulnp to get process names
        res_p = subprocess.run(["ss", "-tulnp"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        lines_p = res_p.stdout.strip().splitlines()
        
        proc_map = {}
        for lp in lines_p[1:]:
            parts = lp.split()
            if len(parts) >= 5:
                proto = parts[0].lower()
                local = parts[4]
                users = " ".join(parts[6:]) if len(parts) > 6 else ""
                proc_map[(proto, local)] = users

        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            proto = parts[0].lower()
            state = parts[1]
            local = parts[4]
            extra = " ".join(parts[5:])
            
            if ":" not in local:
                continue
            ip_part, port_str = local.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                continue
            
            users_info = proc_map.get((proto, local), "")
            
            cgroup_info = ""
            if "cgroup:" in extra:
                cg_match = [p for p in extra.split() if p.startswith("cgroup:")]
                if cg_match:
                    cgroup_info = cg_match[0].replace("cgroup:", "")

            sockets.append({
                "proto": proto,
                "state": state,
                "local_addr": local,
                "ip": ip_part,
                "port": port,
                "users": users_info,
                "cgroup": cgroup_info,
                "extra": extra
            })
    except Exception as e:
        sys.stderr.write(f"Warning: Could not query listening sockets: {e}\n")
    return sockets

def parse_docker_port_mappings(docker_containers: Dict[str, Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Extract mapped host ports from Docker containers."""
    port_to_container = {}
    for name, c_info in docker_containers.items():
        ports_str = c_info.get("Ports", "")
        if not ports_str:
            continue
        mappings = ports_str.split(", ")
        for m in mappings:
            if "->" in m:
                host_part, container_part = m.split("->", 1)
                proto = "tcp"
                if "/" in container_part:
                    _, proto = container_part.split("/", 1)
                if ":" in host_part:
                    h_ip, h_port_str = host_part.rsplit(":", 1)
                    try:
                        h_port = int(h_port_str)
                        if h_port not in port_to_container:
                            port_to_container[h_port] = []
                        port_to_container[h_port].append({
                            "container": name,
                            "image": c_info.get("Image", ""),
                            "status": c_info.get("Status", ""),
                            "state": c_info.get("State", ""),
                            "host_ip": h_ip,
                            "proto": proto,
                            "container_port": container_part
                        })
                    except ValueError:
                        pass
    return port_to_container

def match_service_for_port(port: int, proto: str, registry: Dict[str, Any], docker_ports: Dict[int, List[Dict[str, Any]]], active_socket: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Find what software is running on a port and classify it."""
    # 1. Check selfhosted registry
    services = registry.get("selfhosted_services", [])
    for s in services:
        if port in s.get("ports", []):
            return {
                "name": f"{s.get('icon', '')} {s.get('name', '')}".strip(),
                "category": s.get("category", "Self-Hosted App"),
                "type": "⭐ Self-Hosted Web App",
                "service_id": s.get("id"),
                "description": s.get("description", ""),
                "web_port": s.get("web_port"),
                "protocol": s.get("protocol", "http"),
                "compose_dir": s.get("compose_dir"),
                "config_path": s.get("config_path"),
                "default_creds": s.get("default_creds", ""),
                "is_selfhosted": True
            }
            
    # 2. Check docker mappings
    if port in docker_ports:
        c_list = docker_ports[port]
        c_names = ", ".join(set(c["container"] for c in c_list))
        c_images = ", ".join(set(c["image"] for c in c_list))
        return {
            "name": f"Docker: {c_names}",
            "category": "Containerized Service",
            "type": "🐳 Docker Container",
            "service_id": c_names,
            "description": f"Image: {c_images}",
            "web_port": port,
            "protocol": "http",
            "is_selfhosted": False
        }
        
    # 3. Check known system ports registry
    known_sys = registry.get("known_system_ports", {})
    if str(port) in known_sys:
        ks = known_sys[str(port)]
        return {
            "name": ks.get("name", "System Service"),
            "category": ks.get("category", "Infrastructure"),
            "type": ks.get("type", "🔒 System Daemon"),
            "service_id": str(port),
            "description": ks.get("description", ""),
            "web_port": None,
            "protocol": None,
            "is_selfhosted": False
        }

    # 4. Check active socket info for cgroup / users
    if active_socket:
        users = active_socket.get("users", "")
        cgroup = active_socket.get("cgroup", "")
        if "sshd" in cgroup or "sshd" in users:
            return {
                "name": "OpenSSH Daemon",
                "category": "Remote Shell / SSH",
                "type": "🔒 System Daemon",
                "service_id": "sshd",
                "description": "Secure remote shell access",
                "web_port": None,
                "protocol": None,
                "is_selfhosted": False
            }
        if "tailscaled" in cgroup or "tailscaled" in users:
            return {
                "name": "Tailscale Node Agent",
                "category": "Mesh VPN",
                "type": "🛡️ Infrastructure",
                "service_id": "tailscaled",
                "description": "Tailscale WireGuard mesh networking interface",
                "web_port": None,
                "protocol": None,
                "is_selfhosted": False
            }
        if "docker" in cgroup or "containerd" in cgroup:
            return {
                "name": "Container Runtime Socket",
                "category": "Container Engine",
                "type": "⚙️ System Daemon",
                "service_id": "containerd",
                "description": "Internal container engine communication socket",
                "web_port": None,
                "protocol": None,
                "is_selfhosted": False
            }
        if "agy" in users:
            return {
                "name": "Antigravity CLI IDE Daemon",
                "category": "Developer Tooling",
                "type": "🛠️ Local Process",
                "service_id": "agy",
                "description": "Active Antigravity AI coding agent session socket",
                "web_port": None,
                "protocol": None,
                "is_selfhosted": False
            }

    # 5. Fallback standard socket lookup
    try:
        serv_name = socket.getservbyport(port, proto)
        return {
            "name": f"Service: {serv_name}",
            "category": "Standard Network Port",
            "type": "🌐 Network Service",
            "service_id": serv_name,
            "description": f"Standard {serv_name.upper()} network service",
            "web_port": None,
            "protocol": None,
            "is_selfhosted": False
        }
    except Exception:
        pass

    return {
        "name": "Unknown / Uncataloged",
        "category": "Unregistered",
        "type": "⚠️ Unregistered Service",
        "service_id": f"unknown_{port}",
        "description": "Active socket not cataloged in services.json registry",
        "web_port": None,
        "protocol": None,
        "is_selfhosted": False
    }

def print_header(meta: Optional[Dict[str, Any]] = None):
    resolved = resolve_server_metadata(meta)
    w = min(get_terminal_width(), 138)
    line = "═" * (w - 2)
    print(c(f"╔{line}╗", Color.CYAN))
    title = " 🚀 HOMESERVER PORTEXPLAIN & SELF-HOSTED SOFTWARE INTELLIGENCE "
    padding = max(0, (w - 2 - len(title)) // 2)
    pad_str = " " * padding
    extra_pad = " " * max(0, (w - 2 - len(title)) % 2)
    print(c("║", Color.CYAN) + c(f"{pad_str}{title}{pad_str}{extra_pad}", Color.BOLD + Color.WHITE) + c("║", Color.CYAN))
    
    meta_line = f" Hostname: {resolved['hostname']} | LAN: {resolved['lan_ip']} | Tailscale: {resolved['tailscale_ip']} | Root: {resolved['storage_root']} "
    m_padding = max(0, (w - 2 - len(meta_line)) // 2)
    m_pad = " " * m_padding
    m_extra = " " * max(0, (w - 2 - len(meta_line)) % 2)
    print(c("║", Color.CYAN) + c(f"{m_pad}{meta_line}{m_pad}{m_extra}", Color.DIM + Color.CYAN) + c("║", Color.CYAN))
    print(c(f"╚{line}╝", Color.CYAN))
    print()

def print_hitlist_table(registry: Dict[str, Any], docker_containers: Dict[str, Dict[str, Any]], active_sockets: List[Dict[str, Any]]):
    """Render the Homeserver Self-Hosted Services Master Hit List Table."""
    meta = resolve_server_metadata(registry.get("server_metadata"))
    lan_ip = meta["lan_ip"]
    ts_ip = meta["tailscale_ip"]
    
    services = registry.get("selfhosted_services", [])
    listening_ports = set(s["port"] for s in active_sockets)
    
    print(c("🎯 MASTER SELF-HOSTED SERVICES HIT LIST", Color.BOLD + Color.CYAN))
    print(c("Definitive registry of self-hosted applications running on homeserver", Color.DIM))
    print()
    
    col_app = 22
    col_cat = 22
    col_port = 12
    col_status = 24
    col_lan = 32
    col_ts = 32
    
    header = (
        pad_ansi(c("Application", Color.BOLD), col_app) + " " +
        pad_ansi(c("Category", Color.BOLD), col_cat) + " " +
        pad_ansi(c("Port(s)", Color.BOLD), col_port) + " " +
        pad_ansi(c("Live Status", Color.BOLD), col_status) + " " +
        pad_ansi(c("Local LAN Access URL", Color.BOLD), col_lan) + " " +
        pad_ansi(c("Tailscale Remote Access URL", Color.BOLD), col_ts)
    )
    
    total_w = col_app + col_cat + col_port + col_status + col_lan + col_ts + 5
    separator = "─" * total_w
    print(header)
    print(c(separator, Color.DIM))
    
    for s in services:
        app_name = f"{s.get('icon', '')} {s.get('name', '')}".strip()
        cat = s.get("category", "")
        ports = s.get("ports", [])
        ports_str = ", ".join(str(p) for p in ports) if ports else "Internal"
        web_port = s.get("web_port")
        proto = s.get("protocol", "http") or "http"
        
        # Determine status
        status_text = ""
        stype = s.get("service_type", "docker_compose")
        
        if stype in ["docker_compose", "docker_standalone"]:
            c_names = s.get("container_names", [])
            primary_c = c_names[0] if c_names else s.get("id")
            if primary_c in docker_containers:
                c_info = docker_containers[primary_c]
                c_state = c_info.get("State", "")
                c_status = c_info.get("Status", "")
                
                if "healthy" in c_status:
                    status_text = c("🟢 Up (Healthy)", Color.GREEN)
                elif c_state == "running":
                    status_text = c("🟢 Up (Running)", Color.GREEN)
                elif c_state == "exited":
                    status_text = c("🔴 Stopped (Exited)", Color.RED)
                else:
                    status_text = c(f"🟡 {c_state.capitalize()}", Color.YELLOW)
            else:
                found = False
                for cn in c_names:
                    if cn in docker_containers and docker_containers[cn].get("State") == "running":
                        status_text = c("🟢 Up (Partial)", Color.GREEN)
                        found = True
                        break
                if not found:
                    if web_port and web_port in listening_ports:
                        status_text = c("🟢 Port Active", Color.GREEN)
                    else:
                        status_text = c("🔴 Offline / Not Found", Color.RED)
        elif stype in ["systemd_service", "systemd_user_service"]:
            unit = s.get("systemd_unit", "")
            is_user = (stype == "systemd_user_service")
            if unit:
                is_act, raw_stat = get_systemd_status(unit, user=is_user)
                if is_act:
                    status_text = c(f"🟢 Active ({unit})", Color.GREEN)
                else:
                    if web_port and web_port in listening_ports:
                        status_text = c("🟢 Port Active", Color.GREEN)
                    else:
                        status_text = c(f"🔴 Inactive ({raw_stat})", Color.RED)
            else:
                if web_port and web_port in listening_ports:
                    status_text = c("🟢 Active (Host)", Color.GREEN)
                else:
                    status_text = c("🟡 Standalone", Color.YELLOW)
                    
        # URLs
        if web_port:
            lan_url = f"{proto}://{lan_ip}:{web_port}"
            ts_url = f"{proto}://{ts_ip}:{web_port}"
        else:
            lan_url = c("N/A (Background Service)", Color.DIM)
            ts_url = c("N/A", Color.DIM)
            
        row = (
            pad_ansi(app_name, col_app) + " " +
            pad_ansi(cat, col_cat) + " " +
            pad_ansi(ports_str, col_port) + " " +
            pad_ansi(status_text, col_status) + " " +
            pad_ansi(lan_url, col_lan) + " " +
            pad_ansi(ts_url, col_ts)
        )
        print(row)
    print()

def print_active_listening_sockets(registry: Dict[str, Any], docker_containers: Dict[str, Dict[str, Any]], active_sockets: List[Dict[str, Any]]):
    """Render the Active Listening Network Sockets Breakdown Table."""
    docker_ports = parse_docker_port_mappings(docker_containers)
    
    print(c("🔌 ACTIVE LISTENING NETWORK SOCKETS (REAL-TIME BREAKDOWN)", Color.BOLD + Color.CYAN))
    print(c("Every active listening port on homeserver, mapped to container/process & software function", Color.DIM))
    print()
    
    port_groups = {}
    for s in active_sockets:
        port = s["port"]
        proto = s["proto"].upper()
        key = (port, proto)
        if key not in port_groups:
            port_groups[key] = {
                "port": port,
                "proto": proto,
                "ips": set(),
                "sockets": []
            }
        port_groups[key]["ips"].add(s["ip"])
        port_groups[key]["sockets"].append(s)
        
    sorted_keys = sorted(port_groups.keys(), key=lambda k: (k[0], k[1]))
    
    col_port = 12
    col_bind = 22
    col_service = 28
    col_class = 26
    col_desc = 46
    
    header = (
        pad_ansi(c("Port/Proto", Color.BOLD), col_port) + " " +
        pad_ansi(c("Bind Interface", Color.BOLD), col_bind) + " " +
        pad_ansi(c("Running Software", Color.BOLD), col_service) + " " +
        pad_ansi(c("Classification", Color.BOLD), col_class) + " " +
        pad_ansi(c("Explanation / Purpose", Color.BOLD), col_desc)
    )
    total_w = col_port + col_bind + col_service + col_class + col_desc + 4
    separator = "─" * total_w
    print(header)
    print(c(separator, Color.DIM))
    
    unregistered_alerts = []
    
    for (port, proto) in sorted_keys:
        pdata = port_groups[(port, proto)]
        ips = pdata["ips"]
        
        if "0.0.0.0" in ips and "[::]" in ips:
            bind_str = "All IPv4 & IPv6 (*)"
        elif "0.0.0.0" in ips:
            bind_str = "All IPv4 (0.0.0.0)"
        elif "[::]" in ips:
            bind_str = "All IPv6 ([::])"
        elif "127.0.0.1" in ips:
            bind_str = "Localhost (127.0.0.1)"
        else:
            bind_str = ", ".join(sorted(ips))
            if len(bind_str) > 20:
                bind_str = bind_str[:17] + "..."
                
        port_proto_str = f"{port}/{proto}"
        
        first_sock = pdata["sockets"][0]
        s_info = match_service_for_port(port, proto.lower(), registry, docker_ports, first_sock)
        
        s_name = s_info.get("name", "Unknown")
        s_class = s_info.get("type", "Unknown")
        s_desc = s_info.get("description", "")
        
        if "⭐" in s_class:
            class_colored = c(s_class, Color.GREEN)
        elif "🐳" in s_class:
            class_colored = c(s_class, Color.CYAN)
        elif "🛡️" in s_class or "🔒" in s_class:
            class_colored = c(s_class, Color.BLUE)
        elif "⚙️" in s_class or "⚡" in s_class:
            class_colored = c(s_class, Color.MAGENTA)
        elif "⚠️" in s_class:
            class_colored = c(s_class, Color.YELLOW)
            unregistered_alerts.append((port, proto, s_name, bind_str))
        else:
            class_colored = c(s_class, Color.WHITE)
            
        row = (
            pad_ansi(port_proto_str, col_port) + " " +
            pad_ansi(bind_str, col_bind) + " " +
            pad_ansi(s_name, col_service) + " " +
            pad_ansi(class_colored, col_class) + " " +
            pad_ansi(s_desc, col_desc)
        )
        print(row)
        
    print()
    return unregistered_alerts

def print_audit_summary(registry: Dict[str, Any], docker_containers: Dict[str, Dict[str, Any]], active_sockets: List[Dict[str, Any]], unregistered_alerts: List[Tuple]):
    """Print summary stats, health alerts, and audit recommendations."""
    services = registry.get("selfhosted_services", [])
    listening_ports = set(s["port"] for s in active_sockets)
    
    total_services = len(services)
    online_services = 0
    stopped_services = []
    
    for s in services:
        stype = s.get("service_type", "docker_compose")
        ports = s.get("ports", [])
        
        is_up = False
        if stype in ["docker_compose", "docker_standalone"]:
            for cn in s.get("container_names", []):
                if cn in docker_containers and docker_containers[cn].get("State") == "running":
                    is_up = True
                    break
        elif stype in ["systemd_service", "systemd_user_service"]:
            unit = s.get("systemd_unit", "")
            if unit:
                is_up, _ = get_systemd_status(unit, user=(stype == "systemd_user_service"))
        
        if not is_up and any(p in listening_ports for p in ports):
            is_up = True
            
        if is_up:
            online_services += 1
        else:
            stopped_services.append(s.get("name", s.get("id")))

    print(c("📊 SYSTEM HEALTH & AUDIT SUMMARY", Color.BOLD + Color.CYAN))
    print(f" • Total Self-Hosted Applications : {c(str(total_services), Color.BOLD)}")
    print(f" • Online & Running Services     : {c(str(online_services), Color.GREEN + Color.BOLD)} / {total_services}")
    if stopped_services:
        stopped_str = ", ".join(stopped_services)
        print(f" • Inactive / Stopped Services   : {c(stopped_str, Color.YELLOW)}")
    print(f" • Total Active Listening Sockets : {c(str(len(active_sockets)), Color.CYAN)}")
    print()
    
    if unregistered_alerts:
        print(c("⚠️  UNREGISTERED ACTIVE SOCKETS DETECTED", Color.BOLD + Color.YELLOW))
        print(c("The following ports are currently listening but not cataloged in the Hit List registry:", Color.YELLOW))
        for port, proto, name, bind in unregistered_alerts:
            print(f"   - {c(f'{port}/{proto}', Color.BOLD)}: {name} (Bound: {bind})")
        print(c(f"👉 Action: Review {DOC_REGISTRY_PATH} and add newly deployed services!", Color.CYAN))
        print()
    else:
        print(c("✅ Registry Audit Clean: All active listening application sockets match cataloged services.", Color.GREEN))
        print()

def inspect_single_port_or_name(query: str, registry: Dict[str, Any], docker_containers: Dict[str, Dict[str, Any]], active_sockets: List[Dict[str, Any]]):
    """Inspect a single port or service name in deep detail."""
    meta = resolve_server_metadata(registry.get("server_metadata"))
    lan_ip = meta["lan_ip"]
    ts_ip = meta["tailscale_ip"]
    ts_fqdn = meta["tailscale_fqdn"]
    
    docker_ports = parse_docker_port_mappings(docker_containers)
    listening_ports = {s["port"]: s for s in active_sockets}
    
    target_port = None
    target_service = None
    
    query_clean = query.lstrip(":")
    if query_clean.isdigit():
        target_port = int(query_clean)
    else:
        q_lower = query_clean.lower()
        for s in registry.get("selfhosted_services", []):
            if q_lower == s.get("id", "").lower() or q_lower == s.get("name", "").lower():
                target_service = s
                if s.get("ports"):
                    target_port = s.get("ports")[0]
                break
                
    if not target_service and target_port:
        for s in registry.get("selfhosted_services", []):
            if target_port in s.get("ports", []):
                target_service = s
                break
                
    print(c(f"🔍 PORTEXPLAIN DEEP DIVE: {query}", Color.BOLD + Color.CYAN))
    print("═" * 70)
    
    if target_service:
        s = target_service
        app_name = f"{s.get('icon', '')} {s.get('name', '')}".strip()
        print(f" Application   : {c(app_name, Color.BOLD + Color.WHITE)}")
        print(f" Category      : {s.get('category', '')}")
        print(f" Service ID    : {s.get('id', '')}")
        print(f" Primary Ports : {', '.join(str(p) for p in s.get('ports', []))}")
        
        web_port = s.get("web_port")
        proto = s.get("protocol", "http") or "http"
        if web_port:
            print(f" Local LAN URL : {c(f'{proto}://{lan_ip}:{web_port}', Color.CYAN)}")
            print(f" Tailscale URL : {c(f'{proto}://{ts_ip}:{web_port}', Color.CYAN)}")
            print(f" Tailscale FQDN: {c(f'{proto}://{ts_fqdn}:{web_port}', Color.CYAN)}")
            
        print(f" Description   : {s.get('description', '')}")
        if s.get("default_creds"):
            print(f" Credentials   : {c(s.get('default_creds'), Color.YELLOW)}")
        if s.get("compose_dir"):
            print(f" Compose Stack : {s.get('compose_dir')}")
        if s.get("config_path"):
            print(f" Config Path   : {s.get('config_path')}")
            
        c_names = s.get("container_names", [])
        if c_names:
            print(f" Containers    :")
            for cn in c_names:
                if cn in docker_containers:
                    c_info = docker_containers[cn]
                    c_state = c_info.get("State", "")
                    c_stat = c_info.get("Status", "")
                    c_ports = c_info.get("Ports", "None")
                    state_col = Color.GREEN if c_state == "running" else Color.RED
                    print(f"   • {c(cn, Color.BOLD)} -> {c(c_stat, state_col)} (Ports: {c_ports})")
                else:
                    print(f"   • {cn} -> {c('Not found in docker ps', Color.RED)}")
        print()
    elif target_port:
        print(f" Port Number   : {c(str(target_port), Color.BOLD)}")
        s_info = match_service_for_port(target_port, "tcp", registry, docker_ports)
        print(f" Detected App  : {s_info.get('name')}")
        print(f" Category      : {s_info.get('category')}")
        print(f" Classification: {s_info.get('type')}")
        print(f" Description   : {s_info.get('description')}")
        
        if target_port in listening_ports:
            sock = listening_ports[target_port]
            print(f" Live Socket   : {c('🟢 LISTENING', Color.GREEN)} on {sock['ip']}")
            if sock.get("users"):
                print(f" Process Info  : {sock['users']}")
            if sock.get("cgroup"):
                print(f" Cgroup/Service: {sock['cgroup']}")
        else:
            print(f" Live Socket   : {c('🔴 NOT LISTENING', Color.RED)}")
        print()
    else:
        print(c(f"❌ No service or port found matching query: {query}", Color.RED))
        print("Try running `portexplain` without arguments to see all active ports and services.")
        print()

def add_new_service_interactive():
    """Interactive CLI tool to register a new self-hosted application."""
    print(c("➕ REGISTER NEW SELF-HOSTED SOFTWARE", Color.BOLD + Color.CYAN))
    print("This will add the new service to ~/.config/portexplain/services.json")
    print()
    
    try:
        s_id = input("Service Identifier (e.g. photoprism, nextcloud): ").strip().lower()
        if not s_id:
            print("Cancelled: Service ID is required.")
            return
            
        s_name = input("Display Name (e.g. PhotoPrism): ").strip() or s_id.capitalize()
        s_icon = input("Emoji Icon (e.g. 🖼️, 📦, 🚀) [default: 📦]: ").strip() or "📦"
        s_category = input("Category (e.g. Photos, Storage, Media): ").strip() or "General"
        
        ports_in = input("Port(s) (comma-separated, e.g. 2342): ").strip()
        ports = [int(p.strip()) for p in ports_in.split(",") if p.strip().isdigit()]
        
        web_port = ports[0] if ports else None
        proto = input("Protocol (http/https) [default: http]: ").strip() or "http"
        c_names_in = input("Docker Container Name(s) (comma-separated): ").strip()
        c_names = [c.strip() for c in c_names_in.split(",") if c.strip()]
        
        compose_dir = input("Compose Stack Directory (e.g. /mnt/storage/AppData/...): ").strip() or None
        config_path = input("Configuration File Path: ").strip() or None
        desc = input("Short Description: ").strip()
        creds = input("Default / Initial Credentials: ").strip() or "Standard Setup"
        
        reg = load_registry()
        services = reg.get("selfhosted_services", [])
        
        services = [s for s in services if s.get("id") != s_id]
        
        new_entry = {
            "id": s_id,
            "name": s_name,
            "icon": s_icon,
            "category": s_category,
            "ports": ports,
            "web_port": web_port,
            "protocol": proto,
            "container_names": c_names,
            "service_type": "docker_compose" if c_names else "systemd_service",
            "compose_dir": compose_dir,
            "config_path": config_path,
            "description": desc,
            "default_creds": creds
        }
        
        services.append(new_entry)
        reg["selfhosted_services"] = services
        
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)
            
        print(c(f"✅ Successfully registered {s_name} in {REGISTRY_PATH}!", Color.GREEN))
        print(c(f"Remember to also update {DOC_REGISTRY_PATH} and {DOC_APPS_PATH}!", Color.CYAN))
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")

def main():
    parser = argparse.ArgumentParser(
        description="portexplain - Homeserver Port & Self-Hosted Software Intelligence Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  portexplain               # Full report: Self-hosted Hit List + Active Listening Sockets
  portexplain 8096          # Deep-dive inspection into port 8096 (Jellyfin)
  portexplain immich        # Deep-dive inspection into Immich by name
  portexplain --hitlist     # Show only the master self-hosted software Hit List table
  portexplain --listening   # Show only active listening network sockets
  portexplain --json        # Export complete live server network state as JSON
  portexplain --add         # Interactive registration wizard for new self-hosted apps
"""
    )
    parser.add_argument("query", nargs="?", default=None, help="Port number or service name to inspect (e.g. 8096, 2283, glance)")
    parser.add_argument("-l", "--hitlist", action="store_true", help="Display only the Self-Hosted Applications Master Hit List table")
    parser.add_argument("-p", "--listening", action="store_true", help="Display only the Active Listening Sockets table")
    parser.add_argument("-j", "--json", action="store_true", help="Export live system sockets & self-hosted registry as JSON")
    parser.add_argument("-a", "--audit", action="store_true", help="Run audit checks for uncataloged ports and dead services")
    parser.add_argument("--add", action="store_true", help="Interactive wizard to add a new self-hosted app to registry")
    
    args = parser.parse_args()
    
    if args.add:
        add_new_service_interactive()
        return

    registry = load_registry()
    docker_containers = get_docker_containers()
    active_sockets = get_active_sockets()

    if args.json:
        output_data = {
            "server_metadata": resolve_server_metadata(registry.get("server_metadata")),
            "selfhosted_services": registry.get("selfhosted_services", []),
            "active_listening_sockets": active_sockets,
            "docker_containers": docker_containers
        }
        print(json.dumps(output_data, indent=2))
        return

    if args.query:
        inspect_single_port_or_name(args.query, registry, docker_containers, active_sockets)
        return

    print_header(registry.get("server_metadata"))
    
    if args.hitlist:
        print_hitlist_table(registry, docker_containers, active_sockets)
        return
        
    if args.listening:
        print_active_listening_sockets(registry, docker_containers, active_sockets)
        return

    # Default full view:
    # 1. Initial Hit List (as requested)
    print_hitlist_table(registry, docker_containers, active_sockets)
    
    # 2. Active listening sockets breakdown
    alerts = print_active_listening_sockets(registry, docker_containers, active_sockets)
    
    # 3. Audit & Summary
    print_audit_summary(registry, docker_containers, active_sockets, alerts)

if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
