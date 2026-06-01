FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv .venv \
    && .venv/bin/pip install --no-cache-dir -r requirements.txt \
    && .venv/bin/playwright install webkit --with-deps

COPY . .

CMD ["python3", "-u", "run_loop.py"]
