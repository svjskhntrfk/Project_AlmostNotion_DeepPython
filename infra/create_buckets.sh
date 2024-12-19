#!/bin/sh

set -e

TIMEOUT=30
ELAPSED=0

while ! curl -s http://localhost:9000/minio/health/live; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "Timeout waiting for MinIO to start"
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED+1))
done

BUCKETS=()
while IFS='=' read -r name value; do
    if [ "${name#*_BUCKET}" != "$name" ]; then
        BUCKETS+=("$value")
    fi
done < <(printenv)

# Ожидание запуска MinIO
while ! curl -s http://localhost:9000/minio/health/live; do
    sleep 1
done

# Установка алиаса для MinIO с указанием региона
mc alias set --region ${MINIO_REGION_NAME} myminio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Установка алиаса для MinIO
mc alias set myminio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Создание бакетов и установка анонимных политик доступа
for BUCKET in "${BUCKETS[@]}"; do
    if ! mc ls myminio/${BUCKET} > /dev/null 2>&1; then
        mc mb myminio/${BUCKET}
        mc anonymous set download myminio/${BUCKET}
        echo "Bucket ${BUCKET} created."
    else
        echo "Bucket ${BUCKET} already exists."
    fi
done