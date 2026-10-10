FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FORMAT=json

# tzdata: ZoneInfo needs it for non-UTC send_time timezones.
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY newsletter_machine ./newsletter_machine
COPY config ./config
COPY alembic.ini ./

RUN pip install --no-cache-dir -e . \
    && python -c "import newsletter_machine.cli, newsletter_machine.api.main"

ENV DATABASE_URL=sqlite:///./newsletter_machine.db
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "newsletter_machine.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
