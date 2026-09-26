#!/usr/bin/env bash
# Build the notebook, execute every cell headlessly, and report compactly.
# A cell that raises here is a cell that would raise on molab, which is a
# disqualified submission -- so this runs after every change.
set -uo pipefail
cd "$(dirname "$0")"

OUT=${1:-/tmp/nb_check.html}
BUILD=$(.venv/bin/python build_notebook.py 2>&1) || { echo "BUILD FAILED"; echo "$BUILD"; exit 1; }
echo "$BUILD"

ERR=$(timeout 1200 .venv/bin/python -m marimo export html notebook.py -o "$OUT" --no-include-code 2>&1)
STATUS=$?

FAILS=$(printf '%s\n' "$ERR" | grep -cE "MarimoExceptionRaisedError|MultipleDefinitionError|CycleError|UnparsableError|SyntaxError")
if [ "$FAILS" -gt 0 ]; then
  echo "CELL FAILURES: $FAILS"
  printf '%s\n' "$ERR" | grep -E "Error" | grep -v "An ancestor raised" | sort -u | head -8
  exit 1
fi
[ $STATUS -ne 0 ] && { echo "EXPORT FAILED ($STATUS)"; printf '%s\n' "$ERR" | tail -5; exit 1; }

SIZE=$(( $(stat -c%s "$OUT") / 1024 ))
echo "all cells executed  |  html ${SIZE} KiB"
for m in "${@:2}"; do
  n=$(grep -c -- "$m" "$OUT" 2>/dev/null || echo 0)
  [ "$n" -gt 0 ] && echo "  ok   $m" || { echo "  MISS $m"; exit 1; }
done
exit 0
