FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install CUPS, drivers, AirPrint tools, image/pdf utilities, and Python Flask
RUN apt-get update && apt-get install -y --no-install-recommends \
    cups \
    cups-client \
    cups-filters \
    cups-ipp-utils \
    printer-driver-escpr \
    printer-driver-gutenprint \
    ghostscript \
    poppler-utils \
    imagemagick \
    libcups2 \
    avahi-daemon \
    avahi-utils \
    dbus \
    python3 \
    python3-flask \
    python3-werkzeug \
    curl \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy to allow PDF processing if needed
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' /etc/ImageMagick-6/policy.xml 2>/dev/null || true

# Prepare directories
RUN mkdir -p /app/webprint/templates /app/webprint/static /uploads /etc/cups /var/spool/cups /var/log/cups

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
COPY webprint/ /app/webprint/

RUN chmod +x /entrypoint.sh

EXPOSE 631 8084

ENTRYPOINT ["/entrypoint.sh"]
