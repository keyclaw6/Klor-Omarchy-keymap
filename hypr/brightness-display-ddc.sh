#!/bin/bash
# Both external monitors, one queued DDC worker. No firmware/bridge dependency.
set -euo pipefail

raw_step="${1:-up}"
amount="${2:-5}"
amount="${amount%%%}"
[[ $amount =~ ^[0-9]{1,3}$ ]] || exit 2
case "${raw_step,,}" in
  up|increase|+|plus) step=$((10#$amount));;
  down|decrease|-|minus) step=$((-10#$amount));;
  *)
    if [[ $raw_step =~ ^([0-9]{1,3})%-$ ]]; then
      step=$((-10#${BASH_REMATCH[1]}))
    elif [[ $raw_step =~ ^([+-]?)([0-9]{1,3})%?$ ]]; then
      step=$((10#${BASH_REMATCH[2]}))
      [[ ${BASH_REMATCH[1]} != - ]] || step=$((-step))
    else
      exit 2
    fi
    ;;
esac

# Session-local queue; kernel locks disappear even if the worker is killed.
state_dir="${XDG_RUNTIME_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}}/klor-brightness-ddc"
mkdir -p "$state_dir"
exec 9>"$state_dir/queue.lock"
exec 8>"$state_dir/worker.lock"
flock 9
current=0
[[ ! -s $state_dir/pending ]] || read -r current <"$state_dir/pending"
printf '%s\n' "$((current + step))" >"$state_dir/pending"
if ! flock -n 8; then
  exit 0
fi
flock -u 9

# Discover fresh buses for each worker instead of persisting bus numbers across
# reboots or reconnects. Filter invalid/unsupported DDC displays.
detect_buses() {
  local output
  output=$(timeout 15 ddcutil detect --brief 8>&- 9>&-) || return 1
  mapfile -t buses < <(printf '%s\n' "$output" | awk '
    /^Display [0-9]+/ { valid=1 }
    /^Invalid display/ { valid=0 }
    valid && /I2C bus:/ { sub(/^.*\/dev\/i2c-/, ""); if ($0 ~ /^[0-9]+$/) print }
  ')
  (( ${#buses[@]} > 0 ))
}

apply_bus() {
  local bus=$1 delta=$2 output current maximum target percent attempt
  for attempt in 1 2; do
    if output=$(timeout 5 ddcutil --bus "$bus" getvcp 10 --brief 8>&- 9>&-); then
      break
    fi
    (( attempt < 2 )) || return 1
  done
  read -r current maximum < <(printf '%s\n' "$output" | awk '
    $1 == "VCP" && toupper($2) == "10" && $3 == "C" { print $4, $5; exit }
  ')
  [[ $current =~ ^[0-9]+$ && $maximum =~ ^[0-9]+$ ]] && (( maximum > 0 )) || return 1
  # Delta is percentage points, even for monitors whose VCP maximum isn't 100.
  target=$((current + (delta * maximum / 100)))
  (( target >= 0 )) || target=0
  (( target <= maximum )) || target=$maximum
  # Retry the same absolute target: a timed-out write may already have applied.
  for attempt in 1 2; do
    if timeout 5 ddcutil --bus "$bus" setvcp 10 "$target" --noverify 8>&- 9>&-; then
      percent=$(((target * 100 + maximum / 2) / maximum))
      printf '%s\n' "$percent" >"$state_dir/percent-$bus"
      return 0
    fi
  done
  return 1
}

status=0
buses=()
while true; do
  flock 9
  read -r delta <"$state_dir/pending"
  if (( delta == 0 )); then
    # Release the worker lock while holding the queue lock. An arriving turn
    # must either be consumed here or acquire the worker lock itself.
    flock -u 8
    flock -u 9
    exit "$status"
  fi
  printf '0\n' >"$state_dir/pending"
  flock -u 9

  if (( ${#buses[@]} == 0 )) && ! detect_buses; then
    echo 'KLOR brightness: no accessible DDC monitors detected' >&2
    status=1
    continue
  fi

  pids=()
  for bus in "${buses[@]}"; do
    apply_bus "$bus" "$delta" &
    pids+=("$!")
  done
  failed=0
  for i in "${!pids[@]}"; do
    if ! wait "${pids[$i]}"; then
      echo "KLOR brightness: DDC failed on bus ${buses[$i]}" >&2
      failed=1
      status=1
    fi
  done
  if (( failed )); then
    # Rediscover for the next batch without repeating successful writes.
    buses=()
  elif command -v omarchy-osd >/dev/null 2>&1; then
    percent=$(<"$state_dir/percent-${buses[0]}")
    omarchy-osd -i brightness -p "$percent" 8>&- 9>&- >/dev/null 2>&1 || true
  fi
done
