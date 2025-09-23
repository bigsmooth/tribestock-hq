#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://tribestock-hq.onrender.com}"
TOKENS_FILE="${TOKENS_FILE:-.tokens.env}"

# --- helpers ---
die(){ echo "ERROR: $*" >&2; exit 1; }

json_get(){
  # usage: json_get <field>
  python - "$1" <<'PY'
import sys, json
data = sys.stdin.read()
try:
    obj = json.loads(data)
except Exception as e:
    print(f"__PARSE_ERROR__:{e}")
    sys.exit(2)
field = sys.argv[1]
try:
    print(obj[field])
except KeyError:
    print(f"__MISSING_FIELD__:{field}")
    sys.exit(3)
PY
}

save_tokens(){
  local access="$1" refresh="${2:-}"
  {
    echo "export ACCESS=\"$access\""
    [[ -n "$refresh" ]] && echo "export REFRESH=\"$refresh\""
  } > "$TOKENS_FILE"
  echo "Wrote tokens to $TOKENS_FILE"
}

login(){
  [[ $# -eq 2 ]] || die "Usage: $0 login <username> <password>"
  local user="$1" pass="$2"

  # ask server
  resp=$(curl --fail-with-body -sS -X POST "$BASE_URL/auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$user\",\"password\":\"$pass\"}") || {
      echo "Server response:"; echo "$resp"
      die "login failed"
    }

  # extract
  access=$(printf '%s' "$resp" | json_get access) || true
  refresh=$(printf '%s' "$resp" | json_get refresh) || true

  [[ "$access" != __PARSE_ERROR__:* ]] || { echo "$resp"; die "bad JSON from server"; }
  [[ "$refresh" != __PARSE_ERROR__:* ]] || { echo "$resp"; die "bad JSON from server"; }
  [[ "$access" != __MISSING_FIELD__:* ]] || { echo "$resp"; die "no 'access' in response"; }
  [[ "$refresh" != __MISSING_FIELD__:* ]] || { echo "$resp"; die "no 'refresh' in response"; }

  save_tokens "$access" "$refresh"
  echo "Login OK. Run: source $TOKENS_FILE"
}

refresh_token(){
  # need REFRESH either exported or in file
  if [[ -z "${REFRESH:-}" ]]; then
    [[ -f "$TOKENS_FILE" ]] && source "$TOKENS_FILE" || die "No REFRESH. Run: $0 login <user> <pass>"
  fi

  resp=$(curl --fail-with-body -sS -X POST "$BASE_URL/auth/refresh/" \
    -H "Content-Type: application/json" \
    -d "{\"refresh\":\"$REFRESH\"}") || {
      echo "Server response:"; echo "$resp"
      die "refresh failed"
    }

  access=$(printf '%s' "$resp" | json_get access) || true
  [[ "$access" != __PARSE_ERROR__:* ]] || { echo "$resp"; die "bad JSON from server"; }
  [[ "$access" != __MISSING_FIELD__:* ]] || { echo "$resp"; die "no 'access' in response"; }

  save_tokens "$access" "$REFRESH"
  echo "Refresh OK. Run: source $TOKENS_FILE"
}

me(){
  [[ -n "${ACCESS:-}" ]] || { [[ -f "$TOKENS_FILE" ]] && source "$TOKENS_FILE"; }
  [[ -n "${ACCESS:-}" ]] || die "No ACCESS. Run: $0 login <user> <pass> (then 'source .tokens.env')"
  curl --fail-with-body -sS "$BASE_URL/me/" -H "Authorization: Bearer $ACCESS"
}

get(){
  [[ $# -ge 1 ]] || die "Usage: $0 get <path>"
  [[ -n "${ACCESS:-}" ]] || { [[ -f "$TOKENS_FILE" ]] && source "$TOKENS_FILE"; }
  [[ -n "${ACCESS:-}" ]] || die "No ACCESS. Run: $0 login <user> <pass>"
  curl --fail-with-body -sS "$BASE_URL$1" -H "Authorization: Bearer $ACCESS"
}

post(){
  [[ $# -ge 2 ]] || die "Usage: $0 post <path> '<json>'"
  [[ -n "${ACCESS:-}" ]] || { [[ -f "$TOKENS_FILE" ]] && source "$TOKENS_FILE"; }
  [[ -n "${ACCESS:-}" ]] || die "No ACCESS. Run: $0 login <user> <pass>"
  curl --fail-with-body -sS -X POST "$BASE_URL$1" \
    -H "Authorization: Bearer $ACCESS" \
    -H "Content-Type: application/json" \
    -d "$2"
}

case "${1:-}" in
  login) shift; login "$@";;
  refresh) shift; refresh_token "$@";;
  me) shift; me "$@";;
  get) shift; get "$@";;
  post) shift; post "$@";;
  ""|-h|--help|help)
    cat <<'TXT'
Usage:
  ./get_tokens.sh login <username> <password>
  ./get_tokens.sh refresh
  ./get_tokens.sh me
  ./get_tokens.sh get  /skus/
  ./get_tokens.sh post /inventory/adjust/ '{"hub":1,"sku":1,"direction":"IN","qty":25,"note":"initial stock"}'

Env:
  BASE_URL (default: https://tribestock-hq.onrender.com)
  TOKENS_FILE (default: .tokens.env)
TXT
  ;;
  *) die "Unknown command '$1' (run with --help)";;
esac
