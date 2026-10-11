FROM python:3.11-alpine

LABEL maintainer="Blessen <blessen@homeserver>"
LABEL description="Ultra-lightweight IPTV proxy, playlist optimizer, and Live TV gateway for Jellyfin"

WORKDIR /app

# Run as non-root user for security
RUN addgroup -S iptv && adduser -S iptv -G iptv && \
    mkdir -p /app/data && chown -R iptv:iptv /app

COPY --chown=iptv:iptv app.py /app/app.py

USER iptv

EXPOSE 8484

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8484/health')" || exit 1

ENV PYTHONUNBUFFERED=1 \
    PORT=8484 \
    DATA_DIR=/app/data

CMD ["python3", "/app/app.py"]
