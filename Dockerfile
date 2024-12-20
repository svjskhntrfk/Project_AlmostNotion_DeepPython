FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Используем российское зеркало PyPI
RUN pip install --no-cache-dir -i https://pypi.org/simple/ \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]