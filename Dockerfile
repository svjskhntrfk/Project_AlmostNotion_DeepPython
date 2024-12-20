FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Простая установка без прокси с увеличенным таймаутом
RUN pip install --no-cache-dir --default-timeout=300 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]