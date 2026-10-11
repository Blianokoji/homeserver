#!/usr/bin/env bash
# ==============================================================================
# Generate Homeserver Private Local CA & Multi-Domain SAN Wildcard Certificate
# Validity: 10 Years (3650 days)
# ==============================================================================

set -e

CERT_DIR="${1:-/mnt/storage/AppData/caddy/certs}"
mkdir -p "$CERT_DIR"
chmod 700 "$CERT_DIR"

ROOT_KEY="$CERT_DIR/root.key"
ROOT_CRT="$CERT_DIR/root.crt"
WILDCARD_KEY="$CERT_DIR/wildcard.key"
WILDCARD_CSR="$CERT_DIR/wildcard.csr"
WILDCARD_CRT="$CERT_DIR/wildcard.crt"
SAN_CONF="$CERT_DIR/san.cnf"

if [ -f "$WILDCARD_CRT" ] && [ -f "$WILDCARD_KEY" ] && [ -f "$ROOT_CRT" ]; then
    echo "✓ TLS certificates already present at $CERT_DIR"
    exit 0
fi

echo "==> Generating 10-Year Homeserver Root CA..."
openssl req -x509 -new -nodes -keyout "$ROOT_KEY" -out "$ROOT_CRT" \
    -sha256 -days 3650 \
    -subj "/C=IN/ST=Kerala/L=Homeserver/O=Homeserver Root Authority/CN=Homeserver Internal Root CA"

chmod 400 "$ROOT_KEY"
chmod 644 "$ROOT_CRT"

echo "==> Generating Multi-Domain SAN Wildcard Private Key..."
openssl genrsa -out "$WILDCARD_KEY" 2048
chmod 400 "$WILDCARD_KEY"

LAN_IP="${LAN_IP:-$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")}"
TAILSCALE_IP="${TAILSCALE_IP:-$(tailscale ip -4 2>/dev/null || echo "127.0.0.1")}"
TAILSCALE_DOMAIN="${TAILSCALE_DOMAIN:-$(tailscale status --json 2>/dev/null | grep -o '"DNSName": *"[^"]*"' | head -n1 | cut -d'"' -f4 | sed 's/\.$//' || echo "")}"
if [ -z "$TAILSCALE_DOMAIN" ]; then
    TAILSCALE_DOMAIN="homeserver.ts.net"
fi

cat << EOF > "$SAN_CONF"
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
C = IN
ST = State
L = Homeserver
O = Homeserver Lab
CN = *.${TAILSCALE_DOMAIN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.${TAILSCALE_DOMAIN}
DNS.2 = ${TAILSCALE_DOMAIN}
DNS.3 = *.homeserver
DNS.4 = homeserver
DNS.5 = *.home.arpa
DNS.6 = *.lan
IP.1 = ${TAILSCALE_IP}
IP.2 = ${LAN_IP}
IP.3 = 127.0.0.1
EOF

echo "==> Generating Certificate Signing Request (CSR)..."
openssl req -new -key "$WILDCARD_KEY" -out "$WILDCARD_CSR" -config "$SAN_CONF"

echo "==> Signing SAN Wildcard Certificate with Root CA..."
openssl x509 -req -in "$WILDCARD_CSR" -CA "$ROOT_CRT" -CAkey "$ROOT_KEY" \
    -CAcreateserial -out "$WILDCARD_CRT" -days 3650 -sha256 \
    -extensions req_ext -extfile "$SAN_CONF"

chmod 644 "$WILDCARD_CRT"
rm -f "$WILDCARD_CSR" "$SAN_CONF" "$CERT_DIR"/*.srl

echo "✓ TLS Certificates successfully generated in $CERT_DIR:"
echo "   - Root CA:     $ROOT_CRT"
echo "   - Wildcard:    $WILDCARD_CRT"
