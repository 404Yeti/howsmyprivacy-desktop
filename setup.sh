#!/usr/bin/env bash
# HowsMyPrivacy Desktop Monitor - Installation & Setup Script

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner  
echo -e "${YELLOW}"
cat << 'EOF'
  _  _                   __  __       ___     _                    
 | || |_____ __ _____ __|  \/  |_  _ | _ \_ _(_)_ ____ _ __ _  _  
 | __ / _ \ V  V (_-< '  \ |\/| | || |  _/ '_| \ V / _` / _| || | 
 |_||_\___/\_/\_//__/_|_|_|_|  |_|\_, |_| |_| |_|\_/\__,_\__|\_,_| 
                                  |__/                             
           Desktop Monitor - Automated Setup
EOF
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Check dependencies and run original setup
python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk" 2>/dev/null || {
    echo "Installing dependencies..."
    sudo apt update
    sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0
}

# Make executable
chmod +x "$SCRIPT_DIR/howsmyprivacy-desktop.py" "$SCRIPT_DIR/howsmyprivacy-desktop.sh" 2>/dev/null || true

# Configure autostart
read -p "Enable autostart on boot? [Y/n]: " -r
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    mkdir -p ~/.config/autostart
    cat > ~/.config/autostart/howsmyprivacy.desktop << EOF
[Desktop Entry]
Type=Application
Name=HowsMyPrivacy
Comment=Privacy Posture Monitor
Exec=$SCRIPT_DIR/howsmyprivacy-desktop.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
    echo -e "${GREEN}✓${NC} Autostart configured"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Start HowsMyPrivacy:"
echo "  $SCRIPT_DIR/howsmyprivacy-desktop.sh"
echo ""

read -p "Launch now? [Y/n]: " -r
[[ ! $REPLY =~ ^[Nn]$ ]] && exec "$SCRIPT_DIR/howsmyprivacy-desktop.sh"