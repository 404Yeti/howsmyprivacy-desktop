#!/usr/bin/env bash
# HowsMyPrivacy Desktop Monitor launcher
# Checks dependencies and starts the privacy monitor

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for display server
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "ERROR: No display server detected (\$DISPLAY / \$WAYLAND_DISPLAY not set)."
    echo "HowsMyPrivacy requires a graphical environment."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    echo "Install with: sudo apt install python3"
    exit 1
fi

# Check basic Python GTK dependencies
MISSING=()
python3 -c "import gi" 2>/dev/null || MISSING+=("python3-gi")
python3 -c "import cairo" 2>/dev/null || MISSING+=("python3-gi-cairo")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "ERROR: Missing dependencies: ${MISSING[*]}"
    echo ""
    echo "Install with:"
    echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0"
    exit 1
fi

# Check GTK
if ! python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk" 2>/dev/null; then
    echo "ERROR: GTK 4.0 not found"
    echo ""
    echo "Install with:"
    echo "  sudo apt install gir1.2-gtk-4.0"
    exit 1
fi

# Launch HowsMyPrivacy
exec python3 "$SCRIPT_DIR/howsmyprivacy-desktop.py" "$@"




