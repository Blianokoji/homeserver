#!/bin/bash
set -e

CUPS_USER=${CUPS_USER:-admin}
CUPS_PASSWORD=${CUPS_PASSWORD:-admin}
PRINTER_NAME=${PRINTER_NAME:-Epson_L3110}

echo "==> [CUPS] Initializing Print Server Container..."

# Ensure required system users and groups exist
groupadd -r lpadmin 2>/dev/null || true
groupadd -r lp 2>/dev/null || true

if ! id "$CUPS_USER" &>/dev/null; then
    echo "==> [CUPS] Creating user '$CUPS_USER'..."
    useradd -m -s /bin/bash -g lp -G lpadmin "$CUPS_USER"
fi
echo "$CUPS_USER:$CUPS_PASSWORD" | chpasswd
usermod -aG lpadmin,lp "$CUPS_USER" 2>/dev/null || true

# Prepare cups directories
mkdir -p /etc/cups /var/spool/cups /var/log/cups /uploads /run/cups
chmod 755 /var/spool/cups /var/log/cups /run/cups /uploads
chown root:lp /var/spool/cups /etc/cups

# Setup default cupsd.conf if not present
if [ ! -f /etc/cups/cupsd.conf ]; then
    echo "==> [CUPS] Generating cupsd.conf..."
    cat << 'CUPSD' > /etc/cups/cupsd.conf
LogLevel warn
PageLogFormat
MaxLogSize 10m
Listen 0.0.0.0:631
Listen /run/cups/cups.sock
Browsing Yes
BrowseLocalProtocols dnssd
DefaultAuthType Basic
WebInterface Yes
ServerAlias *

<Location />
  Order allow,deny
  Allow all
</Location>

<Location /admin>
  Order allow,deny
  Allow all
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow all
</Location>

<Location /admin/log>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow all
</Location>

<Policy default>
  JobPrivateAccess default
  JobPrivateValues default
  SubscriptionPrivateAccess default
  SubscriptionPrivateValues default

  <Limit Create-Job Print-Job Print-URI Validate-Job>
    Order deny,allow
    Allow all
  </Limit>

  <Limit Send-Document Send-URI Hold-Job Release-Job Restart-Job Purge-Jobs Set-Job-Attributes Create-Job-Subscription Renew-Subscription Cancel-Subscription Get-Notifications Reprocess-Job Cancel-Current-Job Suspend-Current-Job Resume-Job Cancel-My-Jobs Close-Job CUPS-Move-Job CUPS-Get-Document>
    Order deny,allow
    Allow all
  </Limit>

  <Limit CUPS-Add-Modify-Printer CUPS-Delete-Printer CUPS-Add-Modify-Class CUPS-Delete-Class CUPS-Set-Default CUPS-Get-Devices>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
    Allow all
  </Limit>

  <Limit Pause-Printer Resume-Printer Enable-Printer Disable-Printer Pause-Printer-After-Current-Job Hold-New-Jobs Release-Held-New-Jobs Deactivate-Printer Activate-Printer Restart-Printer Shutdown-Printer Startup-Printer Promote-Job Schedule-Job-After Cancel-Jobs CUPS-Accept-Jobs CUPS-Reject-Jobs>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
    Allow all
  </Limit>

  <Limit Cancel-Job CUPS-Authenticate-Job>
    Order deny,allow
    Allow all
  </Limit>

  <Limit All>
    Order deny,allow
    Allow all
  </Limit>
</Policy>
CUPSD
    chmod 640 /etc/cups/cupsd.conf
    chown root:lp /etc/cups/cupsd.conf
fi

# Setup cups-files.conf if needed
if [ ! -f /etc/cups/cups-files.conf ]; then
    cat << 'FILES' > /etc/cups/cups-files.conf
SystemGroup root lpadmin
AccessLog /var/log/cups/access_log
ErrorLog /var/log/cups/error_log
PageLog /var/log/cups/page_log
FILES
    chmod 640 /etc/cups/cups-files.conf
    chown root:lp /etc/cups/cups-files.conf
fi

# Start dbus if not running and socket doesn't exist
if [ ! -S /var/run/dbus/system_bus_socket ]; then
    mkdir -p /var/run/dbus
    dbus-daemon --system --fork 2>/dev/null || true
fi

# Start CUPS daemon in background
echo "==> [CUPS] Starting CUPS daemon..."
cupsd

# Wait for cupsd to be ready
echo "==> [CUPS] Waiting for CUPS server to respond..."
for i in $(seq 1 30); do
    if lpstat -r &>/dev/null; then
        echo "==> [CUPS] CUPS daemon is active!"
        break
    fi
    sleep 0.5
done

# Discover and configure printer if not yet configured
if ! lpstat -p "$PRINTER_NAME" &>/dev/null; then
    echo "==> [CUPS] Configuring printer '$PRINTER_NAME'..."
    
    # Try to dynamically detect Epson USB URI
    DETECTED_URI=$(lpinfo -v 2>/dev/null | grep -i 'EPSON' | head -n 1 | awk '{print $2}')
    if [ -z "$DETECTED_URI" ]; then
        DETECTED_URI="usb://EPSON/L3110%20Series?serial=5835445A3332383966&interface=1"
    fi
    echo "==> [CUPS] Using Device URI: $DETECTED_URI"

    PPD_MODEL="escpr:0/cups/model/epson-inkjet-printer-escpr/Epson-L3110_Series-epson-escpr-en.ppd"
    
    lpadmin -p "$PRINTER_NAME" -E \
        -v "$DETECTED_URI" \
        -m "$PPD_MODEL" \
        -D "Epson EcoTank L3110" \
        -L "Homeserver USB" \
        -o printer-is-shared=true \
        -o media=A4 2>&1 || true

    lpadmin -d "$PRINTER_NAME" 2>/dev/null || true
    cupsaccept "$PRINTER_NAME" 2>/dev/null || true
    cupsenable "$PRINTER_NAME" 2>/dev/null || true
    echo "==> [CUPS] Printer '$PRINTER_NAME' ready and shared!"
else
    echo "==> [CUPS] Printer '$PRINTER_NAME' is already configured."
    cupsaccept "$PRINTER_NAME" 2>/dev/null || true
    cupsenable "$PRINTER_NAME" 2>/dev/null || true
fi

# Start WebPrint portal
echo "==> [WebPrint] Starting Cloud Web Print portal on port 8084..."
python3 /app/webprint/app.py &
WEBPRINT_PID=$!

echo "==> [CUPS] Print server setup complete."
echo "==> IPP & Admin Web UI : http://0.0.0.0:631"
echo "==> Universal Web Dropzone : http://0.0.0.0:8084"

# Handle graceful shutdown
trap "kill -TERM $WEBPRINT_PID 2>/dev/null; killall cupsd 2>/dev/null; exit 0" SIGINT SIGTERM

# Keep container alive and monitor background jobs
while true; do
    if ! kill -0 $WEBPRINT_PID 2>/dev/null; then
        echo "==> [WebPrint] Restarting WebPrint app..."
        python3 /app/webprint/app.py &
        WEBPRINT_PID=$!
    fi
    if ! lpstat -r &>/dev/null; then
        echo "==> [CUPS] Restarting cupsd..."
        cupsd
    fi
    sleep 5
done
