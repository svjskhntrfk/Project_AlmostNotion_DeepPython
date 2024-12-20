FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Установка пакетов по одному с увеличенным таймаутом
RUN pip install --no-cache-dir --default-timeout=100 fastapi && \
    pip install --no-cache-dir --default-timeout=100 uvicorn && \
    pip install --no-cache-dir --default-timeout=100 sqlalchemy && \
    pip install --no-cache-dir --default-timeout=100 asyncpg && \
    pip install --no-cache-dir --default-timeout=100 alembic && \
    pip install --no-cache-dir --default-timeout=100 python-multipart && \
    pip install --no-cache-dir --default-timeout=100 passlib && \
    pip install --no-cache-dir --default-timeout=100 python-dotenv && \
    pip install --no-cache-dir --default-timeout=100 jinja2

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]