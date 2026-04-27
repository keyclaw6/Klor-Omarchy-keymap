#!/bin/bash
set -euo pipefail

raw_step="${1:-up}"
amount="${2:-5}"
amount="${amount%%%}"

case "${raw_step,,}" in
  up|increase|+|plus)
    step="+$amount"
    ;;
  down|decrease|-|minus)
    step="-$amount"
    ;;
  *)
    if [[ $raw_step =~ ^([0-9]+)%-$ ]]; then
      step="-${BASH_REMATCH[1]}"
    elif [[ $raw_step =~ ^([+-]?[0-9]+)%?$ ]]; then
      step="${BASH_REMATCH[1]}"
    else
      exit 2
    fi
    ;;
esac

if [[ ! $step =~ ^[+-]?[0-9]+$ ]]; then
  exit 2
fi

state_dir="${XDG_CACHE_HOME:-$HOME/.cache}/brightness-display-ddc"
state_lock="$state_dir/state.lock"
pending_file="$state_dir/pending_delta"
worker_file="$state_dir/worker"
bus_file="$state_dir/buses"

mkdir -p "$state_dir"

detect_buses() {
  local detect_output

  detect_output="$(/usr/bin/ddcutil detect --brief 2>/dev/null || true)"
  mapfile -t buses < <(printf '%s\n' "$detect_output" | grep -oE '/dev/i2c-[0-9]+' | sed 's#/dev/i2c-##')

  if (( ${#buses[@]} == 0 )); then
    return 1
  fi

  printf '%s\n' "${buses[@]}" > "$bus_file"
}

load_buses() {
  buses=()

  if [[ -s $bus_file ]]; then
    mapfile -t buses < "$bus_file"
  fi

  if (( ${#buses[@]} == 0 )); then
    detect_buses || return 1
    mapfile -t buses < "$bus_file"
  fi
}

read_first_percent() {
  local output

  output="$(/usr/bin/ddcutil --bus "${buses[0]}" getvcp 10 2>/dev/null || true)"
  if [[ $output =~ current\ value\ =\ *([0-9]+) ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi

  return 1
}

apply_relative_delta() {
  local delta="$1"
  local sign="+"
  local amount="$delta"
  local failures=0
  local percent=""
  local pid
  local attempt
  local -a pids=()

  (( delta == 0 )) && return 0

  load_buses || return 1

  if (( delta < 0 )); then
    sign="-"
    amount=$(( -delta ))
  fi

  for attempt in 0 1; do
    failures=0
    pids=()
    for bus in "${buses[@]}"; do
      /usr/bin/ddcutil --bus "$bus" setvcp 10 "$sign" "$amount" --noverify >/dev/null 2>&1 &
      pids+=("$!")
    done

    for pid in "${pids[@]}"; do
      if ! wait "$pid"; then
        (( failures += 1 ))
      fi
    done

    if (( failures < ${#buses[@]} )) || (( attempt == 1 )); then
      break
    fi

    detect_buses || return 1
    mapfile -t buses < "$bus_file"
  done

  if command -v omarchy-swayosd-brightness >/dev/null 2>&1; then
    percent="$(read_first_percent || true)"
    if [[ -n $percent ]]; then
      omarchy-swayosd-brightness "$percent" >/dev/null 2>&1 || true
    fi
  fi
}

queue_delta() {
  local current=0
  local next
  local became_worker=0

  exec 9> "$state_lock"
  flock 9

  if [[ -f $pending_file ]]; then
    current="$(<"$pending_file")"
  fi

  next=$(( current + step ))
  printf '%s\n' "$next" > "$pending_file"

  if [[ ! -e $worker_file ]]; then
    : > "$worker_file"
    became_worker=1
  fi

  flock -u 9
  exec 9>&-

  (( became_worker == 1 ))
}

take_pending_delta() {
  local delta=0

  exec 9> "$state_lock"
  flock 9

  if [[ -f $pending_file ]]; then
    delta="$(<"$pending_file")"
  fi

  printf '0\n' > "$pending_file"

  if (( delta == 0 )); then
    rm -f "$worker_file"
  fi

  flock -u 9
  exec 9>&-

  printf '%s\n' "$delta"
}

if ! queue_delta; then
  exit 0
fi

while true; do
  delta="$(take_pending_delta)"
  if (( delta == 0 )); then
    break
  fi

  apply_relative_delta "$delta" || true
done
