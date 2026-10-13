FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/app/data/medicines.db
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home-dir /app app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py database.py demo_data.py services.py ./
COPY templates ./templates
COPY static ./static
RUN mkdir -p /app/data && chown -R app:app /app
USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health',timeout=3)" || exit 1
CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
