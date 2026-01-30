# Autostart Configuration

Configure SEC-HUD to launch automatically on boot.

---

## Quick Setup (Desktop Autostart)

**Recommended for most users** - Works with GNOME, KDE, XFCE, etc.

```bash
# 1. Create autostart directory
mkdir -p ~/.config/autostart

# 2. Create autostart entry (replace path!)
cat > ~/.config/autostart/sec-hud.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SEC-HUD
Comment=Cyberpunk Security HUD
Exec=/home/YOUR_USERNAME/tools/sec-hud/sec-hud.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# 3. Replace YOUR_USERNAME with your actual username
sed -i "s|YOUR_USERNAME|$USER|g" ~/.config/autostart/sec-hud.desktop
```

**Done!** Log out and log back in to test.

---

## Alternative Methods

### Method 1: GUI Configuration

Most desktop environments have a "Startup Applications" tool:

**GNOME/Ubuntu:**
1. Open "Startup Applications"
2. Click "Add"
3. Name: `SEC-HUD`
4. Command: `/full/path/to/sec-hud/sec-hud.sh`
5. Comment: `Security Monitor`

**KDE/Kubuntu:**
1. System Settings → Autostart
2. Add → Add Application
3. Browse to `sec-hud.sh`

**XFCE:**
1. Settings → Session and Startup
2. Application Autostart tab
3. Add button
4. Fill in details

---

### Method 2: systemd User Service

**For advanced users** - Better logging and control.

```bash
# 1. Create service directory
mkdir -p ~/.config/systemd/user

# 2. Create service file
cat > ~/.config/systemd/user/sec-hud.service << 'EOF'
[Unit]
Description=SEC-HUD Security Monitor
After=graphical-session.target

[Service]
Type=simple
ExecStart=/full/path/to/sec-hud/sec-hud.sh
Restart=on-failure
RestartSec=10
Environment="DISPLAY=:0"

[Install]
WantedBy=default.target
EOF

# 3. Update path in service file
nano ~/.config/systemd/user/sec-hud.service
# Change /full/path/to/sec-hud/ to your actual path

# 4. Enable and start
systemctl --user daemon-reload
systemctl --user enable sec-hud.service
systemctl --user start sec-hud.service
```

#### systemd Control Commands

```bash
# Check status
systemctl --user status sec-hud

# Start
systemctl --user start sec-hud

# Stop
systemctl --user stop sec-hud

# Restart
systemctl --user restart sec-hud

# View logs
journalctl --user -u sec-hud -f

# Disable autostart
systemctl --user disable sec-hud
```

---

## Startup Delay

If SEC-HUD starts before your network is ready, add a delay:

### Desktop Autostart Method
```bash
# Edit autostart file
nano ~/.config/autostart/sec-hud.desktop

# Change Exec line to:
Exec=bash -c 'sleep 10 && /full/path/to/sec-hud/sec-hud.sh'
```

### systemd Method
```bash
# Edit service file
nano ~/.config/systemd/user/sec-hud.service

# Add before ExecStart:
ExecStartPre=/bin/sleep 10

# Reload
systemctl --user daemon-reload
systemctl --user restart sec-hud
```

---

## Troubleshooting

### Window doesn't appear after login

**Check 1: Verify autostart is configured**
```bash
cat ~/.config/autostart/sec-hud.desktop
# Should show your configuration
```

**Check 2: Check if it's running**
```bash
ps aux | grep sec-hud
# Should show running process
```

**Check 3: Test manual start**
```bash
/path/to/sec-hud/sec-hud.sh
# Does it work manually?
```

**Check 4: Check path is correct**
```bash
# Verify file exists at path in autostart
ls -la /full/path/to/sec-hud/sec-hud.sh
```

---

### Multiple instances running

```bash
# Kill all instances
pkill -f sec-hud-scan

# Check autostart isn't duplicated
ls ~/.config/autostart/*sec-hud*
systemctl --user list-unit-files | grep sec-hud
```

---

### Wrong DISPLAY variable (systemd method)

```bash
# Find your DISPLAY
echo $DISPLAY
# Usually :0 or :1

# Update service file
nano ~/.config/systemd/user/sec-hud.service

# Change to match:
Environment="DISPLAY=:0"

# Reload
systemctl --user daemon-reload
systemctl --user restart sec-hud
```

---

### Doesn't survive suspend/resume

Add to systemd service:

```ini
[Service]
Restart=always
RestartSec=5
```

Then reload:
```bash
systemctl --user daemon-reload
```

---

## Verification

### After Reboot

```bash
# 1. Check if running
ps aux | grep sec-hud

# 2. Should see:
# your_user  1234  0.5  1.2  python3 /path/to/sec-hud-scan.py

# 3. Verify window is visible on screen
```

### Check Logs (systemd only)

```bash
# View recent logs
journalctl --user -u sec-hud --since today

# Follow logs in real-time
journalctl --user -u sec-hud -f
```

---

## Disabling Autostart

### Desktop Autostart
```bash
rm ~/.config/autostart/sec-hud.desktop
```

Or use GUI "Startup Applications" to disable it.

### systemd Service
```bash
systemctl --user stop sec-hud
systemctl --user disable sec-hud
```

---

## Advanced: Conditional Start

Only start if VPN is connected:

```bash
cat > ~/.config/autostart/sec-hud.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SEC-HUD
Exec=bash -c 'if ip a | grep -q tun0; then /path/to/sec-hud/sec-hud.sh; fi'
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
```

Only start on specific days:

```bash
Exec=bash -c 'if [ $(date +%u) -le 5 ]; then /path/to/sec-hud/sec-hud.sh; fi'
# Runs Monday-Friday only
```

---

## Best Practices

✅ **DO:**
- Use full absolute paths
- Test manually before enabling autostart
- Add startup delay if you have slow boot
- Check logs if something goes wrong

❌ **DON'T:**
- Use relative paths (`~/` may not work)
- Run as root (unnecessary and insecure)
- Enable multiple autostart methods (causes duplicates)

---

## Desktop Environment Specific Notes

### GNOME/Ubuntu
- Works perfectly with autostart desktop entry
- May need `gnome-tweaks` to manage startup apps

### KDE Plasma
- Autostart folder works
- Can also use System Settings → Autostart

### XFCE
- Supports autostart directory
- Use Session and Startup settings

### i3/Sway (Tiling WMs)
Add to config file:

```bash
# ~/.config/i3/config (or ~/.config/sway/config)
exec --no-startup-id /path/to/sec-hud/sec-hud.sh
```

### Awesome WM
Add to `rc.lua`:

```lua
awful.spawn.with_shell("/path/to/sec-hud/sec-hud.sh")
```

---

## Multi-Monitor Setup

If using multiple monitors and want specific positioning:

```bash
# Install wmctrl
sudo apt install wmctrl

# Create positioning script
cat > ~/tools/sec-hud/position-window.sh << 'EOF'
#!/bin/bash
sleep 3  # Wait for window
wmctrl -r "SEC-HUD" -e 0,1620,100,300,600  # x,y,width,height
EOF

chmod +x ~/tools/sec-hud/position-window.sh

# Update autostart
Exec=bash -c '/path/to/sec-hud/sec-hud.sh & sleep 3 && /path/to/position-window.sh'
```

---

**Your SEC-HUD will now guard your system 24/7!** 🛡️
