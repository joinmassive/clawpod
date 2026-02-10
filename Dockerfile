FROM node:22-bookworm-slim

# Install Chromium system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libatspi2.0-0 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxkbcommon0 \
    libasound2 libexpat1 libx11-6 libcups2 libdrm2 libpango-1.0-0 \
    libcairo2 fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# Install agent-browser and Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
ENV AGENT_BROWSER_SOCKET_DIR=/tmp/agent-browser

RUN npm install -g agent-browser@latest && \
    agent-browser install && \
    npm cache clean --force && \
    chmod -R o+rx /opt/browsers

# Create non-root user
RUN useradd -m -s /bin/bash appuser

# Create skill directory structure
RUN mkdir -p /home/appuser/.clawpod && \
    chown -R appuser:appuser /home/appuser

# Copy skill files
COPY --chown=appuser:appuser SKILL.md _meta.json /home/appuser/.clawpod/
COPY --chown=appuser:appuser docs/ /home/appuser/.clawpod/docs/
COPY --chown=appuser:appuser tests/ /home/appuser/.clawpod/tests/

# Switch to non-root user
USER appuser
WORKDIR /home/appuser/.clawpod

CMD ["bash", "tests/run_tests.sh"]
