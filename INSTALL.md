# Installation Guide

Complete installation instructions for SEC-HUD.

---

## System Requirements

- **OS:** Linux (X11 or Wayland)
- **Python:** 3.8 or higher
- **Display:** Graphical environment required
- **Memory:** ~50MB RAM
- **CPU:** Minimal (< 1% idle)

### Tested On:
- Kali Linux 2024+
- Ubuntu 22.04+
- Debian 12+
- Parrot OS
- Trace Labs OSINT VM

---

## Dependencies

### Required

```bash
# Debian/Ubuntu/Kali
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Fedora
sudo dnf install python3 python3-gobject gtk4

# Arch
sudo pacman -S python python-gobject gtk4
```

### Optional (for full functionality)

```bash
# System tools
sudo apt install iproute2        # 'ss' command for port scanning
sudo apt install net-tools       # Network utilities
sudo apt install systemd         # Service status checks

# Security tools
sudo apt install ufw             # Firewall detection
sudo apt install tor             # Tor status monitoring
sudo apt install iptables        # Firewall rules

# Clipboard tools
sudo apt install xclip           # X11 clipboard access
# OR
sudo apt install xsel            # Alternative clipboard tool
```

---

## Installation Methods

### Method 1: Git Clone (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/sec-hud.git
cd sec-hud

# Make executable
chmod +x sec-hud.sh sec-hud-scan.py

# Test run
./sec-hud.sh
```

### Method 2: Download Release

```bash
# Download latest release
wget https://github.com/yourusername/sec-hud/archive/refs/tags/v1.0.0.tar.gz

# Extract
tar -xzf v1.0.0.tar.gz
cd sec-hud-1.0.0

# Make executable
chmod +x sec-hud.sh sec-hud-scan.py

# Run
./sec-hud.sh
```

### Method 3: Manual Download

1. Download `sec-hud-scan.py` and `sec-hud.sh`
2. Save to a directory (e.g., `~/tools/sec-hud/`)
3. Make executable: `chmod +x sec-hud.sh sec-hud-scan.py`
4. Run: `./sec-hud.sh`

---

## Installation Locations

### User Installation (Recommended)

```bash
# Install to user directory
mkdir -p ~/.local/opt/sec-hud
cd ~/.local/opt/sec-hud
# ... copy files here

# Add to PATH (optional)
echo 'export PATH="$HOME/.local/opt/sec-hud:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### System-wide Installation

```bash
# Install to /opt (requires sudo)
sudo mkdir -p /opt/sec-hud
sudo cp sec-hud-scan.py sec-hud.sh /opt/sec-hud/
sudo chmod +x /opt/sec-hud/*.{py,sh}

# Create symlink
sudo ln -s /opt/sec-hud/sec-hud.sh /usr/local/bin/sec-hud

# Run from anywhere
sec-hud
```

---

## Verification

### Test Dependencies

```bash
# Test Python
python3 --version
# Should be 3.8+

# Test GTK4
python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print('✓ GTK4 OK')"

# Test Cairo
python3 -c "import cairo; print('✓ Cairo OK')"

# Test all imports
python3 << 'EOF'
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk
import cairo
print("✓ All dependencies OK")
EOF
```

### Test Launcher

```bash
# Run dependency check script
./sec-hud.sh

# Should output:
# Using GTK4 version
# [Window appears]
```

### Test Direct Execution

```bash
# Run Python directly
python3 sec-hud-scan.py

# Should see window appear
# Check terminal for any errors
```

---

## Post-Installation

### Desktop Entry (Optional)

Create a desktop launcher:

```bash
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/sec-hud.desktop << EOF
[Desktop Entry]
Type=Application
Name=SEC-HUD
Comment=Cyberpunk Security HUD
Exec=/full/path/to/sec-hud/sec-hud.sh
Icon=security-high
Terminal=false
Categories=System;Security;Monitor;
Keywords=security;monitor;hud;osint;
EOF

# Update database
update-desktop-database ~/.local/share/applications/
```

Replace `/full/path/to/sec-hud/` with your actual path.

### Autostart (Optional)

To run on login, see [AUTOSTART.md](AUTOSTART.md)

---

## Troubleshooting Installation

### Error: "python3: command not found"

```bash
# Install Python 3
sudo apt install python3
```

### Error: "No module named 'gi'"

```bash
# Install PyGObject
sudo apt install python3-gi
```

### Error: "gi.RepositoryError: Typelib file for namespace 'Gtk' (version '4.0') not found"

```bash
# Install GTK4 bindings
sudo apt install gir1.2-gtk-4.0
```

### Error: "No module named 'cairo'"

```bash
# Install Cairo bindings
sudo apt install python3-gi-cairo
```

### Error: "ERROR: No display server detected"

You're in a terminal-only environment (SSH, TTY). SEC-HUD requires a graphical desktop.

```bash
# Check display
echo $DISPLAY
# Should show `:0` or similar

# If empty, you're not in a GUI session
```

### Error: Permission denied

```bash
# Make files executable
chmod +x sec-hud.sh sec-hud-scan.py
```

---

## Upgrading

### From Git

```bash
cd /path/to/sec-hud
git pull origin main

# Restart SEC-HUD
pkill -f sec-hud-scan
./sec-hud.sh
```

### Manual Upgrade

1. Download new version
2. Backup your config (if modified)
3. Replace files
4. Restart SEC-HUD

---

## Uninstallation

```bash
# Stop running instance
pkill -f sec-hud-scan

# Remove files
rm -rf /path/to/sec-hud

# Remove autostart (if configured)
rm ~/.config/autostart/sec-hud.desktop

# Remove desktop entry (if created)
rm ~/.local/share/applications/sec-hud.desktop
update-desktop-database ~/.local/share/applications/

# Remove from PATH (if added)
# Edit ~/.bashrc and remove the export line
```

---

## Next Steps

- Configure autostart: [AUTOSTART.md](AUTOSTART.md)
- Customize appearance: Edit `sec-hud-scan.py`
- Report issues: [GitHub Issues](https://github.com/yourusername/sec-hud/issues)
- Join community: [Trace Labs](https://www.tracelabs.org/)

---

**Installation complete!** Right-click to close, left-click to drag. 🛡️
