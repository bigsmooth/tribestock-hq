#!/usr/bin/env bash
set -euo pipefail
API=https://tribestock-hq.onrender.com
read -p "User: " U; read -s -p "Pass: " P; echo
resp=$(curl -sS -X POST $API/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"$U\",\"password\":\"$P\"}")
ACCESS=$(jq -r .access <<<"$resp"); REFRESH=$(jq -r .refresh <<<"$resp")
cat > .tokens.env <<EOF
export ACCESS_TOKEN=$ACCESS
export REFRESH_TOKEN=$REFRESH
EOF
echo "Tokens saved to .tokens.env. Run: source .tokens.env"
