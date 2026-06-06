FROM ghcr.io/astral-sh/uv:0.11.19-python3.11-trixie
WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    pkg-config \
    libpq-dev \
    libavif-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    unzip \
    zip \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .

RUN uv pip install -r requirements.txt --system 

COPY src/ .


RUN mkdir -p /app/models/db_schemes/minirag

COPY docker/minirag/alembic.ini /app/models/db_schemes/minirag/alembic.ini

# RUN alembic upgrade head


COPY docker/minirag/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]