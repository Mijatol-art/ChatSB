# Python 3.10-slim: most stable for aiohttp + uvloop wheel availability
FROM python:3.10-slim

# System build deps needed for C extensions (ujson, uvloop, frozenlist, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip toolchain first to avoid legacy metadata errors
RUN pip install --upgrade --no-cache-dir pip setuptools wheel

WORKDIR /app

# Install dependencies separately from code (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application source
COPY . .

CMD ["python", "-u", "main.py"]

