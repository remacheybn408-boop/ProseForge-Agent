# ProseForge Agent runtime image (Task 192).
FROM python:3.11-slim-bookworm

# System deps kept minimal: git for source installs, ca-certificates for TLS.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

# Non-root user avoids bind-mount ownership headaches (uid 1000).
RUN useradd --create-home --uid 1000 pfagent

ENV PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PF_AGENT_WORKSPACE=/data \
    PF_AGENT_SERVICE_PORT=8765

WORKDIR /app
COPY . /app

# Install the package. Build arg selects PyPI (default) or the local source.
ARG PF_AGENT_SOURCE=local
RUN if [ "$PF_AGENT_SOURCE" = "local" ]; then pip install --no-cache-dir /app; else pip install --no-cache-dir proseforge-agent; fi

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /data && chown pfagent:pfagent /data
VOLUME ["/data"]
EXPOSE 8765

USER pfagent
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
