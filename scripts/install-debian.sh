#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="${APP_NAME:-sub-stub}"
APP_USER="${APP_USER:-sub-stub}"
APP_GROUP="${APP_GROUP:-sub-stub}"
INSTALL_DIR="${INSTALL_DIR:-/opt/sub-stub}"
SYSTEMD_UNIT="${SYSTEMD_UNIT:-/etc/systemd/system/sub-stub.service}"
MODE="${1:-auto}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${INSTALL_DIR}/.venv"

log() {
  printf '[%s] %s\n' "$APP_NAME" "$*"
}

die() {
  log "error: $*"
  exit 1
}

need_root() {
  [ "${EUID}" -eq 0 ] || die "run as root"
}

check_platform() {
  if [ ! -r /etc/os-release ]; then
    log "warn: /etc/os-release missing, skip Debian check"
    return
  fi

  # shellcheck disable=SC1091
  . /etc/os-release

  if [ "${ID:-}" != "debian" ]; then
    log "warn: target OS '${ID:-unknown}', script tuned for Debian 13"
    return
  fi

  if [ "${VERSION_ID%%.*}" != "13" ]; then
    log "warn: Debian ${VERSION_ID:-unknown}, script tuned for Debian 13"
  fi
}

resolve_mode() {
  case "$MODE" in
    install|update)
      ;;
    auto)
      if [ -f "${INSTALL_DIR}/app.py" ]; then
        MODE="update"
      else
        MODE="install"
      fi
      ;;
    *)
      die "usage: $0 [install|update|auto]"
      ;;
  esac
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

append_missing_package() {
  local package="$1"
  local existing

  for existing in "${missing_packages[@]:-}"; do
    if [ "$existing" = "$package" ]; then
      return
    fi
  done

  missing_packages+=("$package")
}

detect_missing_packages() {
  local -a missing_packages=()

  have_command python3 || append_missing_package python3
  have_command rsync || append_missing_package rsync

  if have_command python3; then
    python3 -c 'import venv' >/dev/null 2>&1 || append_missing_package python3-venv
  else
    append_missing_package python3-venv
  fi

  [ -e /etc/ssl/certs/ca-certificates.crt ] || append_missing_package ca-certificates

  printf '%s\n' "${missing_packages[@]}"
}

install_packages() {
  local package
  local -a filtered_packages=()
  mapfile -t missing_packages < <(detect_missing_packages)

  for package in "${missing_packages[@]}"; do
    if [ -n "$package" ]; then
      filtered_packages+=("$package")
    fi
  done

  missing_packages=("${filtered_packages[@]}")

  if [ "${#missing_packages[@]}" -eq 0 ]; then
    log "system packages already present"
    return
  fi

  log "installing missing packages: ${missing_packages[*]}"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends "${missing_packages[@]}"
}

ensure_user() {
  getent group "$APP_GROUP" >/dev/null || groupadd --system "$APP_GROUP"

  if ! id -u "$APP_USER" >/dev/null 2>&1; then
    useradd \
      --system \
      --gid "$APP_GROUP" \
      --home-dir "$INSTALL_DIR" \
      --no-create-home \
      --shell /usr/sbin/nologin \
      "$APP_USER"
  fi
}

ensure_layout() {
  install -d -m 0755 "$INSTALL_DIR"
  install -d -m 0755 "$INSTALL_DIR/scripts"
  install -d -m 0755 "$INSTALL_DIR/src"
  install -d -m 0755 "$INSTALL_DIR/templates"
}

install_file() {
  local src="$1"
  local dst="$2"
  local mode="$3"

  install -m "$mode" "$src" "$dst"
}

install_owned_file() {
  local src="$1"
  local dst="$2"
  local mode="$3"

  install -o root -g "$APP_GROUP" -m "$mode" "$src" "$dst"
}

sync_dir() {
  local src="$1"
  local dst="$2"
  rsync -a --delete "$src/" "$dst/"
}

sync_runtime_scripts() {
  rsync -a --delete --exclude 'install-debian.sh' "${REPO_DIR}/scripts/" "${INSTALL_DIR}/scripts/"
}

install_runtime_files() {
  install_file "${REPO_DIR}/app.py" "${INSTALL_DIR}/app.py" 0644
  install_file "${REPO_DIR}/main.py" "${INSTALL_DIR}/main.py" 0644
  install_file "${REPO_DIR}/requirements.txt" "${INSTALL_DIR}/requirements.txt" 0644
  install_file "${REPO_DIR}/sub-stub.service" "${INSTALL_DIR}/sub-stub.service" 0644

  if [ -f "${REPO_DIR}/happ.routing" ]; then
    install_owned_file "${REPO_DIR}/happ.routing" "${INSTALL_DIR}/happ.routing" 0640
  fi

  if [ -f "${REPO_DIR}/incy.routing" ]; then
    install_owned_file "${REPO_DIR}/incy.routing" "${INSTALL_DIR}/incy.routing" 0640
  fi

  if [ -f "${REPO_DIR}/servers" ]; then
    install_owned_file "${REPO_DIR}/servers" "${INSTALL_DIR}/servers" 0640
  fi

  if [ -f "${REPO_DIR}/users" ]; then
    install_owned_file "${REPO_DIR}/users" "${INSTALL_DIR}/users" 0640
  fi

  if [ -f "${REPO_DIR}/.env.example" ]; then
    install_owned_file "${REPO_DIR}/.env.example" "${INSTALL_DIR}/.env.example" 0640
    if [ ! -f "${INSTALL_DIR}/.env" ]; then
      install_owned_file "${REPO_DIR}/.env.example" "${INSTALL_DIR}/.env" 0640
      log "created ${INSTALL_DIR}/.env from .env.example"
    fi
  fi

  sync_runtime_scripts
  sync_dir "${REPO_DIR}/src" "${INSTALL_DIR}/src"
  sync_dir "${REPO_DIR}/templates" "${INSTALL_DIR}/templates"

  find "${INSTALL_DIR}/scripts" -type f -name '*.sh' -exec chmod 0755 {} +
}

update_runtime_files() {
  install_file "${REPO_DIR}/app.py" "${INSTALL_DIR}/app.py" 0644
  install_file "${REPO_DIR}/main.py" "${INSTALL_DIR}/main.py" 0644
  install_file "${REPO_DIR}/requirements.txt" "${INSTALL_DIR}/requirements.txt" 0644

  sync_runtime_scripts
  sync_dir "${REPO_DIR}/src" "${INSTALL_DIR}/src"

  find "${INSTALL_DIR}/scripts" -type f -name '*.sh' -exec chmod 0755 {} +
}

ensure_venv() {
  if [ ! -x "${VENV_DIR}/bin/python3" ]; then
    rm -rf "${VENV_DIR}"
    install -d -o "$APP_USER" -g "$APP_GROUP" -m 0755 "${VENV_DIR}"
    runuser -u "$APP_USER" -- python3 -m venv "${VENV_DIR}"
  fi

  chown -R "$APP_USER:$APP_GROUP" "${VENV_DIR}"

  runuser -u "$APP_USER" -- "${VENV_DIR}/bin/python3" -m pip install --upgrade pip setuptools wheel
  runuser -u "$APP_USER" -- "${VENV_DIR}/bin/python3" -m pip install -r "${INSTALL_DIR}/requirements.txt"
}

validate_env_file() {
  local env_file="${INSTALL_DIR}/.env"

  if [ ! -f "$env_file" ]; then
    log "warn: ${env_file} missing; create it before service start"
    return
  fi

  if ! grep -Eq '^[[:space:]]*SECRET_PATH=' "$env_file"; then
    log "warn: SECRET_PATH missing in ${env_file}"
    return
  fi

  if grep -Eq '^[[:space:]]*SECRET_PATH=your_secret_path_here_change_this[[:space:]]*$' "$env_file"; then
    log "warn: SECRET_PATH still uses placeholder in ${env_file}"
  fi
}

install_unit_if_missing() {
  if [ -e "$SYSTEMD_UNIT" ]; then
    log "unit exists, keep local version: $SYSTEMD_UNIT"
    return
  fi

  install -m 0644 "${REPO_DIR}/sub-stub.service" "$SYSTEMD_UNIT"
}

stop_service_if_active() {
  if systemctl is-active --quiet "${APP_NAME}.service"; then
    SERVICE_WAS_ACTIVE=1
    systemctl stop "${APP_NAME}.service"
  else
    SERVICE_WAS_ACTIVE=0
  fi
}

start_or_restart_service() {
  systemctl daemon-reload

  if [ "$MODE" = "install" ]; then
    systemctl enable --now "${APP_NAME}.service"
    return
  fi

  if [ ! -e "$SYSTEMD_UNIT" ]; then
    log "unit missing, skip systemd restart"
    return
  fi

  if [ "${SERVICE_WAS_ACTIVE:-0}" -eq 1 ]; then
    systemctl start "${APP_NAME}.service"
    return
  fi

  if systemctl is-enabled --quiet "${APP_NAME}.service"; then
    systemctl start "${APP_NAME}.service"
  fi
}

main() {
  need_root
  check_platform
  resolve_mode

  log "mode: ${MODE}"
  install_packages
  ensure_user
  ensure_layout

  if [ "$MODE" = "update" ]; then
    [ -f "${INSTALL_DIR}/app.py" ] || die "update target missing: ${INSTALL_DIR}"
    stop_service_if_active
    update_runtime_files
  else
    install_runtime_files
    install_unit_if_missing
  fi

  ensure_venv
  validate_env_file
  start_or_restart_service

  if [ "$MODE" = "install" ]; then
    log "install done: ${INSTALL_DIR}"
    log "check ${INSTALL_DIR}/.env, users, servers, templates before production use"
  else
    log "update done: ${INSTALL_DIR}"
  fi
}

main "$@"
