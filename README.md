# SEC-HUD

**Cyberpunk Security HUD** - A real-time security posture monitor for your Linux desktop.

![SEC-HUD Screenshot](https://via.placeholder.com/600x800/0a0e17/89d1c9?text=SEC-HUD+Screenshot)

A GTK4 + Cairo desktop widget that continuously monitors your system's security posture with a sleek cyberpunk aesthetic. Features real-time scanning, color-coded status indicators, and a composite security score.

---

## Features

🛡️ **Real-Time Security Monitoring**
- VPN connection status
- Tor service monitoring
- DNS leak detection
- Open ports scanning
- Firewall status
- MAC address randomization
- And more...

🎨 **Cyberpunk Aesthetic**
- Transparent beveled window with neon glow
- Color-coded status indicators (Green/Yellow/Red)
- Animated scanlines and glowing accents
- Monospace font with dotted separators

⚡ **Performance**
- Lightweight and efficient
- Auto-refreshes every 60 seconds
- Non-blocking network checks
- Minimal CPU usage when idle

🎯 **User Experience**
- Frameless, always-on-top window
- Drag to reposition
- Right-click to close
- Autostart on boot support

---

## Security Checks

### Network
- **VPN Status** - Detects tun/wg/tap interfaces
- **Tor Status** - Checks systemd service and port 9050
- **DNS Leak** - Validates privacy DNS vs ISP DNS
- **Public IP** - Fetches current external IP
- **Open Ports** - Lists listening TCP ports
- **Firewall** - Checks ufw/iptables/nftables

### System
- **MAC Address** - Verifies randomization
- **Hostname** - Detects identifiable names
- **SSH Config** - Checks password authentication
- **Kernel ASLR** - Validates address space randomization
- **File Permissions** - Audits /etc/shadow and /etc/passwd

### Privacy
- **Browser Data** - Detects Firefox/Chrome/Chromium/Brave
- **Shell History** - Counts bash/zsh history entries
- **Clipboard** - Checks clipboard contents

---

## Installation

### Prerequisites

```bash
# Debian/Ubuntu/Kali
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Optional tools for full functionality
sudo apt install iproute2 ufw tor xclip
```

### Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/sec-hud.git
cd sec-hud

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ✅ Check and install all dependencies
- ✅ Detect GTK version (3 or 4)
- ✅ Verify Python version
- ✅ Install optional tools (ufw, tor, xclip)
- ✅ Configure autostart on boot
- ✅ Create application menu entry
- ✅ Test that SEC-HUD works

### Manual Install

```bash
# Clone the repository
git clone https://github.com/yourusername/sec-hud.git
cd sec-hud

# Install dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Make executable
chmod +x sec-hud.sh sec-hud-scan.py

# Run it
./sec-hud.sh
```

---

## Usage

### Manual Launch

```bash
# Using the launcher (checks dependencies)
./sec-hud.sh

# Or run Python directly
python3 sec-hud-scan.py
```

### Controls

- **Left-click + Drag** - Move window
- **Right-click** - Close application
- **Auto-refresh** - Every 60 seconds

### Autostart on Boot

```bash
# Create autostart entry
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/sec-hud.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SEC-HUD
Comment=Cyberpunk Security HUD
Exec=/full/path/to/sec-hud/sec-hud.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
```

Replace `/full/path/to/sec-hud/` with your actual installation path.

---

## Configuration

SEC-HUD works out of the box with sensible defaults. Advanced users can modify:

### Window Size
Edit `sec-hud-scan.py`, line 827:
```python
WIDTH = 300  # Change width
```

### Refresh Interval
Edit `sec-hud-scan.py`, line 858:
```python
GLib.timeout_add_seconds(60, self._on_refresh)  # Change 60 to desired seconds
```

### Color Scheme
Edit `sec-hud-scan.py`, lines 44-60:
```python
COLORS = {
    "accent": (0x89 / 255, 0xd1 / 255, 0xc9 / 255),  # Cyan/teal
    # ... modify RGB values
}
```

---

## Troubleshooting

### Window doesn't appear
- Verify you're in a graphical environment: `echo $DISPLAY`
- Check GTK4 installation: `python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print('OK')"`

### "ImportError: Requiring namespace 'Gdk' version '3.0'"
- Your system has GTK4. This version is GTK4-compatible.
- If you somehow got the GTK3 version, ensure you have the latest from this repo.

### Permission errors during scans
- Some checks require root (firewall, certain file permissions)
- This is normal - app shows "yellow" status for unavailable checks
- To get full results: `sudo python3 sec-hud-scan.py` (not recommended for daily use)

### High CPU usage
- Check for runaway threads: `top -p $(pgrep -f sec-hud-scan)`
- Verify network checks aren't timing out repeatedly

### Autostart doesn't work
- Check file exists: `ls ~/.config/autostart/sec-hud.desktop`
- Verify path is correct in desktop file
- Check logs: `journalctl --user -xe | grep -i sec-hud`

---

## Development

### Requirements
- Python 3.8+
- GTK 4.0
- Cairo
- GObject Introspection

### Architecture

```
sec-hud-scan.py
├── SecurityScanner      # Runs all security checks
├── CyberpunkFrame       # Cairo drawing/rendering
├── SecHudWindow         # GTK4 window management
└── SecHudApp            # GTK4 application lifecycle
```

### Adding New Checks

1. Add check method to `SecurityScanner` class:
```python
def check_custom(self) -> SecurityCheck:
    # Your check logic
    return SecurityCheck("Name", "green", "Detail", "Section")
```

2. Add to appropriate runner:
```python
def run_local_checks(self):
    checks = [
        self.check_custom,  # Add here
        # ...
    ]
```

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

---

## Credits

**Created by:** Robbie (Trace Labs)
- GitHub: [@yourusername](https://github.com/yourusername)
- Organization: [Trace Labs](https://www.tracelabs.org/)

**Purpose:** Built for OSINT/DFIR professionals who need continuous security awareness while working on investigations.

---

## License

[Choose your license - MIT recommended]

---

## Roadmap

- [ ] Wayland native support
- [ ] Configuration file (YAML/JSON)
- [ ] Custom check plugins
- [ ] Alert notifications
- [ ] Log/history tracking
- [ ] Multi-profile support
- [ ] Integration with security tools (nmap, wireshark)
- [ ] System tray mode

---

## Screenshots

### Main Display
![Main HUD](https://via.placeholder.com/300x600/0a0e17/89d1c9?text=Main+HUD)

### Network Section
![Network checks](https://via.placeholder.com/300x400/0a0e17/00ff41?text=Network+Checks)

### Privacy Section
![Privacy checks](https://via.placeholder.com/300x400/0a0e17/ff0040?text=Privacy+Checks)

---

## Acknowledgments

- Inspired by cyberpunk aesthetics and terminal-based security tools
- Built for the OSINT/CTI community
- Trace Labs VM contributors and testers

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/sec-hud/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/sec-hud/discussions)
- **Trace Labs:** [tracelabs.org](https://www.tracelabs.org/)

---

**Stay secure. Stay aware. Stay cyberpunk.** 🛡️✨