#!/bin/bash

set -e

API_BASE_URL="http://localhost:4000"
UPLOAD_ENDPOINT="/api/v1/songs/upload"
IRA_FILE_PATH="data_ingest/data_ingest.ira"

if [ ! -f "$IRA_FILE_PATH" ]; then
    echo "Error: IRA file not found at $IRA_FILE_PATH"
    exit 1
fi

echo "Uploading $IRA_FILE_PATH..."

URL="$API_BASE_URL$UPLOAD_ENDPOINT"

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -F "file=@$IRA_FILE_PATH" \
    "$URL")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo "Upload successful!"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
else
    echo "Upload failed!"
    echo "Status: $HTTP_STATUS"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi
