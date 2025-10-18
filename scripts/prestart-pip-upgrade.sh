#!/usr/bin/env bash
set -Eeuo pipefail
TAG=sub-stub-pip-update
VENV=/opt/sub-stub/.venv
PY="$VENV/bin/python3"
PIP="$PY -m pip"
CACHE="${SUBSTUB_CACHE_DIR:-/var/cache/sub-stub}"
STAMP="$CACHE/pip-upgrade.last"
LOCK="$CACHE/pip-upgrade.lock"
REQ=/opt/sub-stub/requirements.txt

mkdir -p "$CACHE"
exec 9>"$LOCK" || { logger -t "$TAG" "lock open failed"; exit 0; }
flock -n 9 || { logger -t "$TAG" "lock held, skip"; exit 0; }

if [ -f "$STAMP" ] && find "$STAMP" -mmin -1440 -print -quit | grep -q .; then
  logger -t "$TAG" "skip: <24h"; exit 0
fi

get_outdated() {
  ( PIP_DEFAULT_TIMEOUT=15 $PIP list --disable-pip-version-check --outdated --format=json 2>/dev/null || echo '[]' ) \
  | "$PY" -c 'import sys,json
try: data=json.load(sys.stdin)
except Exception: data=[]
print(" ".join(sorted({d.get("name","") for d in data if d.get("name")})))' || true
}

before="$(get_outdated || true)"
[ -n "${before:-}" ] && logger -t "$TAG" "outdated before: $(wc -w <<<"$before") -> $before" || logger -t "$TAG" "no outdated before"

PIP_NO_CACHE_DIR=1 PIP_DEFAULT_TIMEOUT=15 $PIP install -q --disable-pip-version-check -U pip setuptools wheel || logger -t "$TAG" "warn: tools upgrade failed"

if [ -f "$REQ" ]; then
  PIP_NO_CACHE_DIR=1 PIP_DEFAULT_TIMEOUT=15 $PIP install -q --disable-pip-version-check -U -r "$REQ" --upgrade-strategy only-if-needed || logger -t "$TAG" "warn: deps upgrade failed"
elif [ -n "${before:-}" ]; then
  PIP_NO_CACHE_DIR=1 PIP_DEFAULT_TIMEOUT=15 $PIP install -q --disable-pip-version-check -U $before || logger -t "$TAG" "warn: bulk upgrade failed"
fi

after="$(get_outdated || true)"
updated="$(comm -23 <(tr ' ' '\n' <<<"${before:-}" | sort -u) <(tr ' ' '\n' <<<"${after:-}" | sort -u) | tr '\n' ' ' | sed 's/ $//')"

if [ -n "${updated:-}" ]; then
  logger -t "$TAG" "updated: $(wc -w <<<"$updated") -> $updated"
else
  [ -z "${before:-}" ] && logger -t "$TAG" "no updates needed" || logger -t "$TAG" "no changes (pinned/constraints)"
fi

touch "$STAMP" || true
exit 0
