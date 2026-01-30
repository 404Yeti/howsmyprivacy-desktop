#!/usr/bin/env bash
# SEC-HUD Installation & Setup Script
# Automated setup for all dependencies and configuration

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << 'EOF'
   _____ ___________     __  ____  ______
  / ___// ____/ ____/    / / / / / / / __ \
  \__ \/ __/ / /  ______/ /_/ / / / / / / /
 ___/ / /___/ /__/_____/ __  / /_/ / /_/ /
/____/_____/\____/    /_/ /_/\____/_____/

     Cyberpunk Security HUD - Setup
EOF
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging
LOG_FILE="$SCRIPT_DIR/setup.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "Setup started at $(date)"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Step counter
STEP=1

print_step() {
    echo -e "${BLUE}[Step $STEP/$1]${NC} $2"
    ((STEP++))
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    echo "Run as your regular user: ./setup.sh"
    exit 1
fi

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

detect_os
print_step 10 "Detected OS: $OS $VERSION"

# Check display server
print_step 10 "Checking display server..."
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    print_error "No display server detected"
    echo "SEC-HUD requires a graphical environment (X11 or Wayland)"
    echo "You cannot run this in SSH or TTY without X11 forwarding"
    exit 1
fi
print_success "Display server available: ${DISPLAY:-$WAYLAND_DISPLAY}"

# Check Python version
print_step 10 "Checking Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    echo ""
    echo "Install with:"
    echo "  sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 8 ]; then
    print_error "Python 3.8+ required (found $PYTHON_VERSION)"
    exit 1
fi
print_success "Python $PYTHON_VERSION"

# Check dependencies
print_step 10 "Checking dependencies..."

MISSING_DEPS=()

# Check Python packages
python3 -c "import gi" 2>/dev/null || MISSING_DEPS+=("python3-gi")
python3 -c "import cairo" 2>/dev/null || MISSING_DEPS+=("python3-gi-cairo")

# Check GTK
GTK_VERSION=""
if python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk" 2>/dev/null; then
    GTK_VERSION="4"
    python3 -c "import gi; gi.require_version('Gdk','4.0')" 2>/dev/null || MISSING_DEPS+=("gir1.2-gtk-4.0")
elif python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null; then
    GTK_VERSION="3"
    python3 -c "import gi; gi.require_version('Gdk','3.0')" 2>/dev/null || MISSING_DEPS+=("gir1.2-gtk-3.0")
else
    MISSING_DEPS+=("gir1.2-gtk-4.0")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_warning "Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Would you like to install missing dependencies now?"
    read -p "Install dependencies? [Y/n]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_step 10 "Installing dependencies..."
        
        case $OS in
            ubuntu|debian|kali)
                sudo apt update
                sudo apt install -y ${MISSING_DEPS[@]}
                ;;
            fedora)
                sudo dnf install -y $(echo ${MISSING_DEPS[@]} | sed 's/gir1.2-gtk/gtk/g' | sed 's/-gi//g')
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm python-gobject gtk4
                ;;
            *)
                print_error "Unsupported OS for automatic installation"
                echo "Please install manually:"
                echo "  ${MISSING_DEPS[@]}"
                exit 1
                ;;
        esac
        
        print_success "Dependencies installed"
    else
        print_error "Cannot continue without dependencies"
        exit 1
    fi
else
    print_success "All required dependencies present"
fi

# Verify GTK version
if [ -n "$GTK_VERSION" ]; then
    print_success "GTK $GTK_VERSION available"
else
    # Recheck after installation
    if python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk" 2>/dev/null; then
        GTK_VERSION="4"
    elif python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null; then
        GTK_VERSION="3"
    else
        print_error "GTK still not available after installation"
        exit 1
    fi
fi

# Check optional dependencies
print_step 10 "Checking optional dependencies..."
OPTIONAL_MISSING=()

command -v ss &> /dev/null || OPTIONAL_MISSING+=("iproute2")
command -v ufw &> /dev/null || OPTIONAL_MISSING+=("ufw")
command -v tor &> /dev/null || OPTIONAL_MISSING+=("tor")
command -v xclip &> /dev/null && command -v xsel &> /dev/null || OPTIONAL_MISSING+=("xclip")

if [ ${#OPTIONAL_MISSING[@]} -gt 0 ]; then
    print_warning "Optional tools missing: ${OPTIONAL_MISSING[*]}"
    echo ""
    echo "These tools enable additional security checks:"
    echo "  - iproute2: Port scanning (ss command)"
    echo "  - ufw: Firewall detection"
    echo "  - tor: Tor service monitoring"
    echo "  - xclip: Clipboard monitoring"
    echo ""
    read -p "Install optional tools? [Y/n]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        case $OS in
            ubuntu|debian|kali)
                sudo apt install -y ${OPTIONAL_MISSING[@]}
                ;;
            fedora)
                sudo dnf install -y ${OPTIONAL_MISSING[@]}
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm ${OPTIONAL_MISSING[@]}
                ;;
        esac
        print_success "Optional tools installed"
    else
        print_warning "Skipping optional tools (some checks will show warnings)"
    fi
else
    print_success "All optional tools present"
fi

# Make scripts executable
print_step 10 "Setting permissions..."
chmod +x "$SCRIPT_DIR/sec-hud-scan.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/sec-hud.sh" 2>/dev/null || true
print_success "Scripts are executable"

# Test run
print_step 10 "Testing SEC-HUD..."
echo "Attempting to start SEC-HUD (will close in 3 seconds)..."

if [ -f "$SCRIPT_DIR/sec-hud.sh" ]; then
    LAUNCHER="$SCRIPT_DIR/sec-hud.sh"
elif [ -f "$SCRIPT_DIR/sec-hud-scan.py" ]; then
    LAUNCHER="python3 $SCRIPT_DIR/sec-hud-scan.py"
else
    print_error "Cannot find SEC-HUD executable"
    exit 1
fi

# Start in background
$LAUNCHER &
PID=$!
sleep 3

# Check if still running
if ps -p $PID > /dev/null 2>&1; then
    print_success "SEC-HUD started successfully"
    kill $PID 2>/dev/null || true
    sleep 1
else
    print_error "SEC-HUD failed to start"
    echo "Check the log file: $LOG_FILE"
    exit 1
fi

# Configure autostart
echo ""
print_step 10 "Configuring autostart..."
echo ""
echo "Would you like SEC-HUD to start automatically on boot?"
read -p "Enable autostart? [Y/n]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    mkdir -p ~/.config/autostart
    
    cat > ~/.config/autostart/sec-hud.desktop << EOF
[Desktop Entry]
Type=Application
Name=SEC-HUD
Comment=Cyberpunk Security HUD
Exec=$SCRIPT_DIR/sec-hud.sh
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=System;Security;
EOF
    
    chmod +x ~/.config/autostart/sec-hud.desktop
    print_success "Autostart configured"
    
    # Optional: Add delay
    echo ""
    read -p "Add 10-second startup delay? (useful if network is slow) [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i "s|Exec=$SCRIPT_DIR/sec-hud.sh|Exec=bash -c 'sleep 10 \&\& $SCRIPT_DIR/sec-hud.sh'|g" ~/.config/autostart/sec-hud.desktop
        print_success "Added 10-second startup delay"
    fi
else
    print_warning "Autostart not configured (you can set it up later)"
fi

# Create desktop entry (optional)
echo ""
read -p "Create application menu entry? [Y/n]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    mkdir -p ~/.local/share/applications
    
    cat > ~/.local/share/applications/sec-hud.desktop << EOF
[Desktop Entry]
Type=Application
Name=SEC-HUD
Comment=Cyberpunk Security HUD - Security Monitor
Exec=$SCRIPT_DIR/sec-hud.sh
Icon=security-high
Terminal=false
Categories=System;Security;Monitor;
Keywords=security;monitor;hud;osint;cybersecurity;
EOF
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    fi
    
    print_success "Application menu entry created"
fi

# Summary
echo ""
echo -e "${CYAN}=== Setup Complete ===${NC}"
echo ""
print_success "SEC-HUD is ready to use!"
echo ""
echo "Location: $SCRIPT_DIR"
echo "GTK Version: $GTK_VERSION"
echo "Python: $PYTHON_VERSION"
echo ""

echo "Usage:"
echo "  Manual start:    $SCRIPT_DIR/sec-hud.sh"
if [ -f ~/.config/autostart/sec-hud.desktop ]; then
    echo "  Autostart:       Enabled (starts on next login)"
fi
if [ -f ~/.local/share/applications/sec-hud.desktop ]; then
    echo "  App menu:        Available in Applications → System"
fi
echo ""

echo "Controls:"
echo "  Left-click + drag  = Move window"
echo "  Right-click        = Close application"
echo "  Auto-refresh       = Every 60 seconds"
echo ""

echo "Documentation:"
echo "  Installation:  ${SCRIPT_DIR}/INSTALL.md"
echo "  Autostart:     ${SCRIPT_DIR}/AUTOSTART.md"
echo "  Setup log:     ${LOG_FILE}"
echo ""

# Start now?
read -p "Start SEC-HUD now? [Y/n]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    print_success "Starting SEC-HUD..."
    echo ""
    exec $LAUNCHER
else
    echo ""
    echo "To start SEC-HUD later:"
    echo "  $SCRIPT_DIR/sec-hud.sh"
    echo ""
    echo -e "${GREEN}Enjoy your cyberpunk security monitoring! 🛡️${NC}"
fi
