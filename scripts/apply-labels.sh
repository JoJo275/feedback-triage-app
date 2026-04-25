#!/usr/bin/env bash
set -euo pipefail

# Wrapper around scripts/apply_labels.py
#
# Usage:
#   ./scripts/apply-labels.sh baseline
#   ./scripts/apply-labels.sh extended
#   ./scripts/apply-labels.sh baseline OWNER/REPO
#   ./scripts/apply-labels.sh baseline --dry-run
#
# NOTE (Windows users): The first time you run a .sh file on Windows, the OS
#   may prompt you to choose a program to open it with. Select "Git Bash"
#   (or the Git for Windows bash executable). That first launch only
#   registers the file association — the script itself won't execute.
#   Run the .sh file a second time and it will work. Alternatively, run
#   it directly from Git Bash:  ./scripts/apply-labels.sh extended

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SET="${1:-}"
shift || true
EXTRA_ARGS=("$@")

if [[ -z "${SET}" || ! "${SET}" =~ ^(baseline|extended)$ ]]; then
  echo "Usage: $0 {baseline|extended} [OWNER/REPO] [--dry-run]" >&2
  exit 2
fi

echo "Applying ${SET} labels… (this may take a moment)"
python3 "${SCRIPT_DIR}/apply_labels.py" --set "${SET}" "${EXTRA_ARGS[@]}"
EXIT_CODE=$?

# If launched by double-clicking on Windows, the Git Bash window closes
# instantly — pause so the user can read the output.
if [[ -n "${SESSIONNAME:-}" || "${OS:-}" == "Windows_NT" ]]; then
  echo ""
  read -r -p "Press Enter to close this window..."
fi

exit "${EXIT_CODE}"
