# Dockerfile for AI Project Agent
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (optional; keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: show help if no args
ENTRYPOINT ["python", "src/app.py"]
CMD ["--help"]
