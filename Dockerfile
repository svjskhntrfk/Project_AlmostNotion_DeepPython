FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Установка через прокси
ENV HTTP_PROXY="http://proxy.example.com:8080"
ENV HTTPS_PROXY="http://proxy.example.com:8080"

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]