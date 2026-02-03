# HowsMyPrivacy - Desktop Monitor

<div align="center">

![HowsMyPrivacy Logo](https://via.placeholder.com/200x200/000000/fcc800?text=👁️)

**Real-time privacy and security posture monitoring for Linux desktops**

Part of the **HowsMyPrivacy** family - A suite of local posture-checking tools for desktops, browsers, and mobile devices.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GTK](https://img.shields.io/badge/GTK-4.0-green.svg)](https://www.gtk.org/)

</div>

---

## 🔍 What is HowsMyPrivacy?

**HowsMyPrivacy** is a family of privacy and security monitoring tools designed to give you instant visibility into your digital security posture. The Desktop Monitor is a lightweight, always-on display that continuously checks your Linux system for privacy and security issues.

### The HowsMyPrivacy Family

- **🖥️ Desktop Monitor** (this repo) - Linux desktop security HUD
- **🌐 Browser Extension** (coming soon) - Real-time browser privacy checks
- **📱 Mobile App** (coming soon) - Mobile device security monitoring

---

## ✨ Features

### 🛡️ Real-Time Monitoring
- **VPN Status** - Instant VPN connection detection
- **Tor Monitoring** - Track Tor service status and connectivity
- **DNS Leak Protection** - Verify privacy DNS vs ISP DNS
- **Open Ports** - Scan for listening services
- **Firewall Status** - Check active firewall protection
- **MAC Randomization** - Verify network anonymity
- **And 8 more checks...**

### 🎨 Privacy-First Design
- Minimalist black & gold aesthetic
- Always-on-top, non-intrusive display
- Color-coded status indicators (🟢 Green / 🟡 Yellow / 🔴 Red)
- Composite privacy score (0-100)
- Zero data collection - everything runs locally

### ⚡ Performance
- Lightweight (~50MB RAM)
- Auto-refreshes every 60 seconds
- Non-blocking network checks
- Minimal CPU usage (<1% idle)

### 🎯 User Experience
- Drag to reposition anywhere
- Right-click to close
- Autostart on boot support
- Works on X11 and Wayland

---

## 📊 Privacy Checks

### Network Privacy
| Check | What It Does |
|-------|-------------|
| **VPN Status** | Detects tun/wg/tap VPN interfaces |
| **Tor Status** | Monitors Tor service and SOCKS port |
| **DNS Leak** | Validates use of privacy DNS providers |
| **Public IP** | Shows your current external IP address |
| **Open Ports** | Lists listening TCP services |
| **Firewall** | Checks ufw/iptables/nftables status |

### System Security
| Check | What It Does |
|-------|-------------|
| **MAC Address** | Verifies hardware address randomization |
| **Hostname** | Detects identifiable machine names |
| **SSH Config** | Checks password authentication settings |
| **Kernel ASLR** | Validates memory address randomization |
| **File Permissions** | Audits critical system file permissions |

### Privacy Indicators
| Check | What It Does |
|-------|-------------|
| **Browser Data** | Detects Firefox/Chrome/Chromium/Brave traces |
| **Shell History** | Counts command history entries |
| **Clipboard** | Monitors clipboard data exposure |

---

## 🚀 Quick Start

### Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/howsmyprivacy-desktop.git
cd howsmyprivacy-desktop

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script automatically:
- ✅ Installs all dependencies
- ✅ Detects your GTK version
- ✅ Tests the application
- ✅ Configures autostart (optional)
- ✅ Creates app menu entry (optional)

### Manual Installation

```bash
# Install dependencies (Ubuntu/Debian/Kali)
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Optional: Security tools for full functionality
sudo apt install iproute2 ufw tor xclip

# Run HowsMyPrivacy
python3 howsmyprivacy-desktop.py
```

---

## 📖 Documentation

- **[Installation Guide](INSTALL.md)** - Detailed setup instructions
- **[Autostart Guide](AUTOSTART.md)** - Configure automatic startup
- **[Contributing](#-contributing)** - Help improve HowsMyPrivacy

---

## 🎮 Usage

### Launch
```bash
./howsmyprivacy-desktop.sh
```

### Controls
- **Left-click + Drag** - Move the monitor window
- **Right-click** - Close the application
- **Auto-refresh** - Updates every 60 seconds

### Interpreting Your Score

| Score | Status | Meaning |
|-------|--------|---------|
| 70-100 | 🟢 Good | Strong privacy posture |
| 40-69 | 🟡 Fair | Some improvements needed |
| 0-39 | 🔴 Poor | Significant privacy gaps |

---

## 🔧 Configuration

### Change Refresh Interval

Edit `howsmyprivacy-desktop.py`, line ~858:
```python
GLib.timeout_add_seconds(60, self._on_refresh)  # Change 60 to desired seconds
```

### Customize Colors

Edit `howsmyprivacy-desktop.py`, lines 44-60:
```python
COLORS = {
    "accent": (0xfc / 255, 0xc8 / 255, 0x00 / 255),  # HowsMyPrivacy gold
    # ... modify other colors
}
```

### Window Size

Edit `howsmyprivacy-desktop.py`, line ~827:
```python
WIDTH = 300  # Adjust width in pixels
```

---

## 🐛 Troubleshooting

### Window doesn't appear
```bash
# Check display server
echo $DISPLAY

# Verify GTK4 installation
python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print('✓ OK')"
```

### Permission errors during checks
Some checks (firewall, file permissions) require elevated privileges. This is normal - the app will show yellow warnings for unavailable checks.

### Autostart not working
```bash
# Verify autostart file
cat ~/.config/autostart/howsmyprivacy.desktop

# Check logs
journalctl --user -xe | grep -i privacy
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

---

## 🏗️ Technical Details

### Architecture
```
howsmyprivacy-desktop.py
├── SecurityScanner      # Executes privacy/security checks
├── CyberpunkFrame       # Cairo rendering engine
├── SecHudWindow         # GTK4 window management
└── HowsMyPrivacyApp     # Application lifecycle
```

### Requirements
- **Python**: 3.8 or higher
- **GTK**: 4.0 (GTK 3.0 compatible version available)
- **Cairo**: Graphics rendering
- **Linux**: X11 or Wayland display server

### Supported Distributions
- ✅ Kali Linux 2024+
- ✅ Ubuntu 22.04+
- ✅ Debian 12+
- ✅ Parrot OS
- ✅ Fedora 38+
- ✅ Arch Linux
- ✅ Any modern Linux with GTK4

---

## 🤝 Contributing

We welcome contributions to HowsMyPrivacy! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/new-check`)
3. **Add** your privacy check or improvement
4. **Test** thoroughly on multiple distributions
5. **Submit** a pull request

### Adding New Privacy Checks

```python
def check_custom(self) -> SecurityCheck:
    """Add your custom privacy check here"""
    # Your check logic
    return SecurityCheck("Check Name", "green", "Detail", "Section")
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Logo Design**: HowsMyPrivacy "privacy eye" concept
- **Inspired by**: Terminal-based security tools and privacy-first design principles
- **Community**: OSINT, InfoSec, and privacy advocacy communities

---

## 🌟 Roadmap

### Current Version (v1.0)
- ✅ Desktop monitor for Linux
- ✅ 14+ privacy checks
- ✅ Real-time monitoring
- ✅ Autostart support

### Upcoming Features
- [ ] **Browser Extension** - Real-time browser privacy monitoring
- [ ] **Mobile App** - Android/iOS privacy checks
- [ ] **Configuration File** - YAML-based settings
- [ ] **Custom Plugins** - User-defined privacy checks
- [ ] **Alert Notifications** - Desktop notifications for privacy breaches
- [ ] **Privacy Log** - Historical tracking and trends
- [ ] **Multi-Profile Support** - Work/Personal/Anonymous profiles
- [ ] **Network Monitor Integration** - Deep packet inspection
- [ ] **System Tray Mode** - Minimize to tray

---

## 📱 Stay Connected

- **Website**: [howsmyprivacy.org](https://howsmyprivacy.org) *(coming soon)*
- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Issues**: [Report a bug](https://github.com/yourusername/howsmyprivacy-desktop/issues)
- **Discussions**: [Join the community](https://github.com/yourusername/howsmyprivacy-desktop/discussions)

---

## 💡 Philosophy

**Your privacy is your right.** HowsMyPrivacy believes in:

- 🔒 **Privacy by design** - No telemetry, no data collection
- 💻 **Local-first** - All checks run on your machine
- 🌐 **Open source** - Transparent and auditable code
- 🆓 **Free forever** - Privacy tools should be accessible to everyone
- 🛡️ **User empowerment** - Knowledge is the first step to privacy

---

## 🎯 Why HowsMyPrivacy?

In an age of constant surveillance, you deserve to know your privacy posture at a glance. HowsMyPrivacy gives you:

- **Instant visibility** into your privacy status
- **Proactive monitoring** to catch issues before they matter
- **Peace of mind** knowing your defenses are up
- **Educational insight** into privacy best practices

Whether you're a privacy advocate, security professional, journalist, activist, or just privacy-conscious - HowsMyPrivacy has your back.

---

<div align="center">

**🛡️ Know your privacy. Protect your future. 🛡️**

*Made with 💛 for the privacy-conscious community*

</div>