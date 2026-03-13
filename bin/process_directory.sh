#!/usr/bin/env bash

set -euo pipefail
shopt -s nullglob

process_matches() {
  local directory

  for directory in *YTS.MX* *YTS.LT*; do
    [[ -d "${directory}" ]] || continue
    "${HOME}/process_torrent.sh" "${directory}"
  done
}

while true; do
  process_matches
  sleep 300
done
