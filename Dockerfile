FROM python:3.11-slim

WORKDIR /app

# Установка только необходимых системных пакетов
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements.txt сначала
COPY requirements.txt .

# Устанавливаем зависимости с оптимизациями
RUN pip install --no-cache-dir -r requirements.txt \
    --compile \
    --no-deps \
    --disable-pip-version-check

COPY . .
RUN mkdir -p static

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]