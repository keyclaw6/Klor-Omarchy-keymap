#!/usr/bin/env bash
# ============================================================================
# 05_git_lockdown.sh — Git commit lockdown for KLOR 4K ASCII layout project
# ============================================================================
#
# Purpose: Stage and commit the 5-phase documentation set (00-04) that
#          produces the 4K ASCII terminal cheat sheet for the KLOR Polydactyl
#          split keyboard.
#
# Artifact integrity:
#   04_4k_klor_layout.txt
#     Lines:     166
#     Max width: 175 chars
#     SHA256:    fcaab44e2f941d201b100ed5c5a6c780acbd1628c56f6229f2ce0be29101badf
#
# This script is idempotent — re-running after commit produces no side effects.
# ============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

FILES=(
  00_state_and_todo_log.md
  01_klor_extraction_map.md
  02_ascii_scale_strategy.md
  03_validation_audit.md
  04_4k_klor_layout.txt
  ASCII_LAYOUT.txt
  05_git_lockdown.sh
)

EXPECTED_SHA="fcaab44e2f941d201b100ed5c5a6c780acbd1628c56f6229f2ce0be29101badf"

# --- Pre-flight: verify ASCII art file integrity ---
ACTUAL_SHA="$(sha256sum 04_4k_klor_layout.txt | awk '{print $1}')"
if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]]; then
  echo "FATAL: 04_4k_klor_layout.txt SHA256 mismatch!"
  echo "  Expected: $EXPECTED_SHA"
  echo "  Got:      $ACTUAL_SHA"
  exit 1
fi
echo "SHA256 integrity check PASSED for 04_4k_klor_layout.txt"

# --- Pre-flight: verify all files exist ---
for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "FATAL: Missing file: $f"
    exit 1
  fi
done
echo "All ${#FILES[@]} files present."

# --- Stage and commit ---
git add "${FILES[@]}"

# Check if there is anything to commit
if git diff --cached --quiet; then
  echo "Nothing new to commit — files already committed."
  exit 0
fi

git commit -m "docs: add 5-phase KLOR 4K ASCII layout extraction (00-04)

Phase 00: State log and hardware identity (KLOR Polydactyl, RP2040)
Phase 01: Exhaustive extraction — 42 keys x 5 layers, encoders, command mode, prompts, snippets
Phase 02: ASCII scaling strategy — 4K terminal math (175 cols x 166 rows)
Phase 03: Validation audit — 7 cross-reference checks, all passing
Phase 04: 4K ASCII art cheat sheet — the primary deliverable (166 lines, 175 chars wide)

Also includes ASCII_LAYOUT.txt and this lockdown script (05)."

echo ""
echo "Commit successful. Current HEAD:"
git log --oneline -1
