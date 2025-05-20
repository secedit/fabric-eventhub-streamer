#!/bin/bash

# Docker imajını oluştur
docker build -t fabric-eventhub-streamer .

# Docker konteynerini çalıştır
docker run -it --rm \
  -e FABRIC_EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -e FABRIC_EVENTHUB_NAME="your-eventhub-name" \
  -e ZIP_FILES="/app/data1/trip_*.zip,/app/data2/trip_*.zip" \
  -e BATCH_SIZE="1000" \
  -e SEND_INTERVAL="0.1" \
  -e MAX_RETRIES="3" \
  -e MAX_CONCURRENT_FILES="10" \
  -v /path/to/your/zip/files1:/app/data1 \
  -v /path/to/your/zip/files2:/app/data2 \
  fabric-eventhub-streamer
