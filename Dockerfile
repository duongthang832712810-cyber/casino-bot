# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first for better Docker layer caching.
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy application source.
COPY bot.py ./bot.py
COPY src ./src
COPY tests ./tests

# Runtime SQLite data and generated backup files live here.
RUN mkdir -p /app/data /app/logs

# Run as a non-root user for safer containers.
RUN adduser --disabled-password --gecos "" --home /app casino \
    && chown -R casino:casino /app
USER casino

# Required environment variables:
# - DISCORD_TOKEN: Discord bot token.
# - OWNER_ID: Discord user ID allowed to use /backup commands.
# Optional environment variables:
# - COMMAND_PREFIX: Prefix commands, default !
# - DATABASE_PATH: SQLite path, default data/bot.sqlite3
# - LOG_LEVEL: INFO/DEBUG/WARNING/ERROR, default INFO
# - SYNC_COMMANDS: true/false, default true
#
# Mount /app/data as a volume to persist SQLite data across container restarts:
# docker run --env-file .env -v casino-data:/app/data casino-bot
VOLUME ["/app/data", "/app/logs"]

CMD ["python", "bot.py"]
