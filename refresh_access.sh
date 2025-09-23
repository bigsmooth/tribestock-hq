#!/usr/bin/env bash
set -euo pipefail
API=https://tribestock-hq.onrender.com
: "${REFRESH_TOKEN:?source .tokens.env first}"
ACCESS=$(curl -sS -X POST $API/auth/refresh/ -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH_TOKEN\"}" | jq -r .access)
export ACCESS_TOKEN="$ACCESS"
echo "ACCESS_TOKEN refreshed."
