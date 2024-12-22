#!/bin/sh

/usr/bin/mc config host add myminio http://minio:9000 minioadmin minioadmin
/usr/bin/mc mb myminio/media --ignore-existing
/usr/bin/mc policy set public myminio/media 