#!/usr/bin/env bash
# SEC-HUD launcher - checks dependencies and starts the HUD

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for display server
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "ERROR: No display server detected (\$DISPLAY / \$WAYLAND_DISPLAY not set)."
    echo "SEC-HUD requires a graphical environment."
    exit 1
fi

# Check Python GTK dependencies
MISSING=()
python3 -c "import gi" 2>/dev/null || MISSING+=("python3-gi")
python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null || MISSING+=("gir1.2-gtk-3.0")
python3 -c "import cairo" 2>/dev/null || MISSING+=("python3-gi-cairo")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "ERROR: Missing dependencies: ${MISSING[*]}"
    echo ""
    echo "Install with:"
    echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
    exit 1
fi

exec python3 "$SCRIPT_DIR/sec-hud-scan.py" "$@"
