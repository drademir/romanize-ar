FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CAMELTOOLS_DATA=/opt/camel_tools_data

WORKDIR /app

# System deps for camel-tools (numpy/scipy wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Download MLE disambiguator model (~500MB). Fails silently if offline —
# service falls back to rule-only mode.
RUN camel_data -i disambig-mle-calima-msa-r13 || echo "camel_data download failed; rule-only mode"

COPY app ./app
COPY data ./data

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "2"]
