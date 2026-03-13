#!/usr/bin/env bash
#
# Copies a directory with a movie file to the FreeBSD server for storage.
#

set -euo pipefail

previous_message=""
logrepeat=0
active_user=""

get_active_user() {
  active_user="$(scutil <<< "show State:/Users/ConsoleUser" | awk '/Name :/ && ! /loginwindow/ { print $3 }')"
}

emit_log() {
  local message timestamp

  message="$1"
  timestamp="$(date -u +%F' '%T)"
  get_active_user

  echo "${timestamp}:${active_user}[$$] : ${message}"
  logger -i "${message}"
  if command -v say >/dev/null 2>&1; then
    say "${message}"
  fi
}

print_log() {
  local message

  message="$*"
  if [[ -z "${message}" ]]; then
    return
  fi

  if [[ "${message}" == "${previous_message}" ]]; then
    ((logrepeat += 1))
    return
  fi

  if (( logrepeat > 0 )); then
    emit_log "Last message repeated {${logrepeat}} times"
    logrepeat=0
  fi

  emit_log "${message}"
  previous_message="${message}"
}

flush_log_repeats() {
  if (( logrepeat > 0 )); then
    emit_log "Last message repeated {${logrepeat}} times"
    logrepeat=0
  fi
}

has_video_files() {
  local torrent_path

  torrent_path="$1"
  compgen -G "${torrent_path}/*.mkv" >/dev/null || \
    compgen -G "${torrent_path}/*.avi" >/dev/null || \
    compgen -G "${torrent_path}/*.mp4" >/dev/null
}

torrentpath=""
if [[ $# -ge 3 ]]; then
  torrentpath="$3"
elif [[ $# -ge 1 ]]; then
  torrentpath="$1"
elif [[ -n "${TR_TORRENT_DIR:-}" ]]; then
  torrentpath="${TR_TORRENT_DIR}"
else
  print_log "Usage: $0 <folder name>"
  exit 1
fi

if [[ -d "${torrentpath}" ]] && has_video_files "${torrentpath}"; then
  print_log "Processing ${torrentpath}"
  sleep 3
  print_log "Starting transfer"
  if rsync -avz -- "${torrentpath}" "rdottin@192.168.1.188:/zroot/movies/completed-movies"; then
    rm -rf -- "${torrentpath}"
    print_log "Transfer complete"
  else
    print_log "An error occurred during transfer"
    exit 1
  fi
else
  print_log "Unable to find video file in ${torrentpath}."
  exit 1
fi

flush_log_repeats
