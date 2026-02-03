#!/usr/bin/env python3
"""HowsMyPrivacy Desktop Monitor

A privacy and security posture monitor for Linux desktops.
Part of the HowsMyPrivacy family - local posture-checking tools
for desktops, browsers, and mobile devices.

Positioned on the right side of the desktop, auto-refreshes every 60s,
and rates security with color indicators plus a composite score.
"""

import math
import os
import re
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

# GTK4 imports - must specify versions BEFORE any other gi imports
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk

import cairo


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SecurityCheck:
    name: str
    status: str  # "green", "yellow", "red"
    detail: str
    section: str  # "Network", "System", "Privacy"


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

COLORS = {
    "accent":     (0xfc / 255, 0xc8 / 255, 0x00 / 255),   # #fcc800 - HowsMyPrivacy Gold
    "bg_dark":    (0x0a / 255, 0x0a / 255, 0x0a / 255),    # #0a0a0a - Pure black
    "bg_panel":   (0x15 / 255, 0x15 / 255, 0x15 / 255),    # #151515 - Dark gray
    "green":      (0x00 / 255, 0xff / 255, 0x41 / 255),    # #00ff41 - Matrix green
    "yellow":     (0xfc / 255, 0xc8 / 255, 0x00 / 255),    # #fcc800 - Brand yellow
    "red":        (0xff / 255, 0x00 / 255, 0x40 / 255),    # #ff0040 - Alert red
    "dim":        (0.40, 0.40, 0.35),
    "text":       (0.85, 0.85, 0.80),
    "text_bright": (0.95, 0.95, 0.90),
}

STATUS_COLORS = {
    "green":  COLORS["green"],
    "yellow": COLORS["yellow"],
    "red":    COLORS["red"],
}


# ---------------------------------------------------------------------------
# Security scanner  (no GTK dependency)
# ---------------------------------------------------------------------------

PRIVACY_DNS = {
    "9.9.9.9", "9.9.9.10", "9.9.9.11", "9.9.9.12",        # Quad9
    "149.112.112.112",
    "1.1.1.1", "1.0.0.1",                                    # Cloudflare
    "208.67.222.222", "208.67.220.220",                       # OpenDNS
    "8.8.8.8", "8.8.4.4",                                    # Google (public)
    "45.90.28.0", "45.90.30.0",                               # NextDNS
    "94.140.14.14", "94.140.15.15",                           # AdGuard
}

KNOWN_DEFAULT_HOSTNAMES = re.compile(
    r"^(localhost|kali|parrot|ubuntu|debian|raspberrypi|"
    r"tracelabs|pc|desktop|laptop|user)$",
    re.IGNORECASE,
)

IDENTIFIABLE_HOSTNAME = re.compile(
    r"[A-Z][a-z]+[-_ ][A-Z][a-z]+",  # e.g. "John-Doe"
)


class SecurityScanner:
    """Runs all security checks."""

    def __init__(self):
        self.checks: List[SecurityCheck] = []
        self.score: int = 0
        self.scan_time: str = ""

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _run(cmd: str, timeout: int = 5) -> Optional[str]:
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return r.stdout.strip()
        except Exception:
            return None

    @staticmethod
    def _read(path: str) -> Optional[str]:
        try:
            with open(path) as f:
                return f.read()
        except Exception:
            return None

    # -- individual checks ------------------------------------------------

    def check_vpn(self) -> SecurityCheck:
        try:
            net_dir = "/sys/class/net"
            if not os.path.isdir(net_dir):
                return SecurityCheck("VPN Status", "yellow", "Cannot read net info", "Network")
            ifaces = os.listdir(net_dir)
            vpn_ifaces = [i for i in ifaces if i.startswith(("tun", "wg", "tap"))]
            if vpn_ifaces:
                # check if UP
                for vi in vpn_ifaces:
                    operstate = self._read(f"{net_dir}/{vi}/operstate")
                    if operstate and operstate.strip() == "up":
                        return SecurityCheck("VPN Status", "green", f"{vi} UP", "Network")
                return SecurityCheck("VPN Status", "yellow", f"{', '.join(vpn_ifaces)} down", "Network")
            return SecurityCheck("VPN Status", "red", "No VPN found", "Network")
        except Exception:
            return SecurityCheck("VPN Status", "yellow", "Error", "Network")

    def check_tor(self) -> SecurityCheck:
        try:
            active = self._run("systemctl is-active tor 2>/dev/null")
            if active == "active":
                # verify port
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                try:
                    s.connect(("127.0.0.1", 9050))
                    s.close()
                    return SecurityCheck("Tor Status", "green", "Running :9050", "Network")
                except Exception:
                    s.close()
                    return SecurityCheck("Tor Status", "green", "Active (port N/A)", "Network")
            # check if installed
            which = self._run("which tor 2>/dev/null")
            if which:
                return SecurityCheck("Tor Status", "yellow", "Installed, stopped", "Network")
            return SecurityCheck("Tor Status", "red", "Not found", "Network")
        except Exception:
            return SecurityCheck("Tor Status", "yellow", "Error", "Network")

    def check_dns(self) -> SecurityCheck:
        try:
            resolv = self._read("/etc/resolv.conf")
            if not resolv:
                return SecurityCheck("DNS Leak", "yellow", "Cannot read resolv.conf", "Network")
            nameservers = re.findall(r"nameserver\s+(\S+)", resolv)
            if not nameservers:
                return SecurityCheck("DNS Leak", "yellow", "No nameservers", "Network")
            ns_display = ", ".join(nameservers[:2])
            if len(nameservers) > 2:
                ns_display += "..."
            # check if privacy DNS
            if any(ns in PRIVACY_DNS for ns in nameservers):
                return SecurityCheck("DNS Leak", "green", ns_display, "Network")
            # WSL proxy pattern (172.x, 10.x, 192.168.x)
            wsl_pattern = re.compile(r"^(172\.(1[6-9]|2\d|3[01])|10\.|192\.168\.)")
            if any(wsl_pattern.match(ns) for ns in nameservers):
                return SecurityCheck("DNS Leak", "yellow", f"WSL proxy {ns_display}", "Network")
            return SecurityCheck("DNS Leak", "red", f"ISP DNS {ns_display}", "Network")
        except Exception:
            return SecurityCheck("DNS Leak", "yellow", "Error", "Network")

    def check_public_ip(self) -> SecurityCheck:
        """Run via thread (network call)."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://ifconfig.me", headers={"User-Agent": "curl/7.88"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                ip = resp.read().decode().strip()
            return SecurityCheck("Public IP", "yellow", ip, "Network")
        except Exception:
            return SecurityCheck("Public IP", "yellow", "Unavailable", "Network")

    def check_open_ports(self) -> SecurityCheck:
        try:
            out = self._run("ss -tlnp 2>/dev/null")
            if out is None:
                return SecurityCheck("Open Ports", "yellow", "ss unavailable", "Network")
            lines = [l for l in out.splitlines()[1:] if l.strip()]
            n = len(lines)
            detail = f"{n} listening"
            if n <= 3:
                return SecurityCheck("Open Ports", "green", detail, "Network")
            if n <= 5:
                return SecurityCheck("Open Ports", "yellow", detail, "Network")
            return SecurityCheck("Open Ports", "red", detail, "Network")
        except Exception:
            return SecurityCheck("Open Ports", "yellow", "Error", "Network")

    def check_firewall(self) -> SecurityCheck:
        try:
            # try ufw first
            ufw = self._run("ufw status 2>/dev/null")
            if ufw and "active" in ufw.lower() and "inactive" not in ufw.lower():
                return SecurityCheck("Firewall", "green", "ufw active", "Network")
            # try iptables
            ipt = self._run("iptables -L -n 2>/dev/null")
            if ipt is not None:
                rules = [l for l in ipt.splitlines() if l and not l.startswith(("Chain", "target"))]
                if rules:
                    return SecurityCheck("Firewall", "green", f"iptables {len(rules)} rules", "Network")
            # try nftables
            nft = self._run("nft list ruleset 2>/dev/null")
            if nft and len(nft.splitlines()) > 2:
                return SecurityCheck("Firewall", "green", "nftables active", "Network")
            # check if we just lack perms
            if ipt is None and nft is None:
                return SecurityCheck("Firewall", "yellow", "Needs root", "Network")
            return SecurityCheck("Firewall", "red", "No firewall", "Network")
        except Exception:
            return SecurityCheck("Firewall", "yellow", "Error", "Network")

    def check_mac_address(self) -> SecurityCheck:
        try:
            net_dir = "/sys/class/net"
            if not os.path.isdir(net_dir):
                return SecurityCheck("MAC Address", "yellow", "Cannot read", "System")
            for iface in sorted(os.listdir(net_dir)):
                if iface == "lo":
                    continue
                assign_type = self._read(f"{net_dir}/{iface}/addr_assign_type")
                if assign_type is None:
                    continue
                val = assign_type.strip()
                if val in ("1", "3"):  # random/set
                    return SecurityCheck("MAC Address", "green", f"{iface} randomized", "System")
            return SecurityCheck("MAC Address", "red", "Hardware MAC", "System")
        except Exception:
            return SecurityCheck("MAC Address", "yellow", "Error", "System")

    def check_hostname(self) -> SecurityCheck:
        try:
            hostname = socket.gethostname()
            if IDENTIFIABLE_HOSTNAME.search(hostname):
                return SecurityCheck("Hostname", "red", hostname, "System")
            if KNOWN_DEFAULT_HOSTNAMES.match(hostname):
                return SecurityCheck("Hostname", "yellow", f"{hostname} (default)", "System")
            return SecurityCheck("Hostname", "green", hostname, "System")
        except Exception:
            return SecurityCheck("Hostname", "yellow", "Error", "System")

    def check_ssh_config(self) -> SecurityCheck:
        try:
            # check if sshd is running
            sshd_active = self._run("systemctl is-active sshd 2>/dev/null || systemctl is-active ssh 2>/dev/null")
            if sshd_active and "inactive" in sshd_active:
                return SecurityCheck("SSH Config", "green", "sshd stopped", "System")
            if sshd_active and "active" not in sshd_active:
                return SecurityCheck("SSH Config", "green", "sshd not running", "System")
            cfg = self._read("/etc/ssh/sshd_config")
            if cfg is None:
                return SecurityCheck("SSH Config", "yellow", "Cannot read config", "System")
            pwd_match = re.search(r"^\s*PasswordAuthentication\s+(yes|no)", cfg, re.MULTILINE | re.IGNORECASE)
            if pwd_match:
                if pwd_match.group(1).lower() == "no":
                    return SecurityCheck("SSH Config", "green", "PwdAuth off", "System")
                return SecurityCheck("SSH Config", "red", "PwdAuth on", "System")
            return SecurityCheck("SSH Config", "yellow", "Default config", "System")
        except Exception:
            return SecurityCheck("SSH Config", "yellow", "Error", "System")

    def check_aslr(self) -> SecurityCheck:
        try:
            val = self._read("/proc/sys/kernel/randomize_va_space")
            if val is None:
                return SecurityCheck("Kernel ASLR", "yellow", "Cannot read", "System")
            v = val.strip()
            if v == "2":
                return SecurityCheck("Kernel ASLR", "green", "Full (2)", "System")
            if v == "1":
                return SecurityCheck("Kernel ASLR", "yellow", "Partial (1)", "System")
            return SecurityCheck("Kernel ASLR", "red", f"Disabled ({v})", "System")
        except Exception:
            return SecurityCheck("Kernel ASLR", "yellow", "Error", "System")

    def check_file_perms(self) -> SecurityCheck:
        try:
            issues = []
            shadow = "/etc/shadow"
            if os.path.exists(shadow):
                st = os.stat(shadow)
                mode = st.st_mode & 0o777
                if mode & 0o004:  # world-readable
                    issues.append("shadow world-read")
            passwd = "/etc/passwd"
            if os.path.exists(passwd):
                st = os.stat(passwd)
                mode = st.st_mode & 0o777
                if mode & 0o002:  # world-writable
                    issues.append("passwd world-write")
            if issues:
                return SecurityCheck("File Perms", "red", ", ".join(issues), "System")
            return SecurityCheck("File Perms", "green", "Correct", "System")
        except Exception:
            return SecurityCheck("File Perms", "yellow", "Error", "System")

    def check_browser_data(self) -> SecurityCheck:
        try:
            home = os.path.expanduser("~")
            browser_paths = [
                ("Firefox", os.path.join(home, ".mozilla", "firefox")),
                ("Chrome", os.path.join(home, ".config", "google-chrome")),
                ("Chromium", os.path.join(home, ".config", "chromium")),
                ("Brave", os.path.join(home, ".config", "BraveSoftware")),
            ]
            found = []
            for name, path in browser_paths:
                if os.path.isdir(path):
                    found.append(name)
            if found:
                return SecurityCheck("Browser Data", "red", ", ".join(found), "Privacy")
            return SecurityCheck("Browser Data", "green", "No data found", "Privacy")
        except Exception:
            return SecurityCheck("Browser Data", "yellow", "Error", "Privacy")

    def check_shell_history(self) -> SecurityCheck:
        try:
            home = os.path.expanduser("~")
            hist_files = [
                os.path.join(home, ".bash_history"),
                os.path.join(home, ".zsh_history"),
            ]
            max_lines = 0
            for hf in hist_files:
                if os.path.isfile(hf):
                    try:
                        with open(hf, errors="replace") as f:
                            lines = sum(1 for _ in f)
                        max_lines = max(max_lines, lines)
                    except Exception:
                        pass
            if max_lines == 0:
                return SecurityCheck("Shell History", "green", "No history", "Privacy")
            if max_lines < 50:
                return SecurityCheck("Shell History", "yellow", f"{max_lines} entries", "Privacy")
            return SecurityCheck("Shell History", "red", f"{max_lines} entries", "Privacy")
        except Exception:
            return SecurityCheck("Shell History", "yellow", "Error", "Privacy")

    def check_clipboard(self) -> SecurityCheck:
        try:
            # try xclip
            clip = self._run("xclip -selection clipboard -o 2>/dev/null")
            if clip is None:
                clip = self._run("xsel --clipboard --output 2>/dev/null")
            if clip is None:
                return SecurityCheck("Clipboard", "green", "No tool / empty", "Privacy")
            if clip.strip():
                length = len(clip.strip())
                return SecurityCheck("Clipboard", "yellow", f"{length} chars", "Privacy")
            return SecurityCheck("Clipboard", "green", "Empty", "Privacy")
        except Exception:
            return SecurityCheck("Clipboard", "green", "N/A", "Privacy")

    # -- aggregate runners ------------------------------------------------

    def run_local_checks(self) -> List[SecurityCheck]:
        checks = []
        local_methods = [
            self.check_vpn,
            self.check_tor,
            self.check_dns,
            self.check_open_ports,
            self.check_firewall,
            self.check_mac_address,
            self.check_hostname,
            self.check_ssh_config,
            self.check_aslr,
            self.check_file_perms,
            self.check_browser_data,
            self.check_shell_history,
            self.check_clipboard,
        ]
        for method in local_methods:
            try:
                checks.append(method())
            except Exception:
                name = method.__name__.replace("check_", "").replace("_", " ").title()
                checks.append(SecurityCheck(name, "yellow", "Error", "System"))
        return checks

    def run_network_checks(self) -> List[SecurityCheck]:
        checks = []
        try:
            checks.append(self.check_public_ip())
        except Exception:
            checks.append(SecurityCheck("Public IP", "yellow", "Error", "Network"))
        return checks

    def calculate_score(self) -> int:
        if not self.checks:
            return 0
        values = {"green": 100, "yellow": 50, "red": 0}
        total = sum(values.get(c.status, 50) for c in self.checks)
        return round(total / len(self.checks))

    def run_all(self):
        self.checks = self.run_local_checks()
        net_checks = self.run_network_checks()
        # insert network checks after existing network checks
        net_idx = 0
        for i, c in enumerate(self.checks):
            if c.section == "Network":
                net_idx = i + 1
        for nc in net_checks:
            self.checks.insert(net_idx, nc)
            net_idx += 1
        self.score = self.calculate_score()
        self.scan_time = time.strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Cyberpunk Cairo drawing
# ---------------------------------------------------------------------------

class CyberpunkFrame:
    """Handles all Cairo drawing for the HUD."""

    CORNER_CUT = 18
    PADDING = 14
    LINE_HEIGHT = 20
    HEADER_FONT_SIZE = 15
    BODY_FONT_SIZE = 11.5
    SCORE_FONT_SIZE = 42

    def __init__(self):
        self.width = 300
        self._cached_height = 600

    def measure_height(self, checks: List[SecurityCheck]) -> int:
        """Calculate total height needed."""
        y = self.PADDING + 40  # header area
        y += 70  # score area
        y += 10  # spacing

        sections_seen = set()
        for c in checks:
            if c.section not in sections_seen:
                sections_seen.add(c.section)
                y += 30  # section header
            y += self.LINE_HEIGHT

        y += 30  # footer
        y += self.PADDING
        self._cached_height = max(y, 200)
        return self._cached_height

    @property
    def height(self):
        return self._cached_height

    # -- drawing primitives -----------------------------------------------

    @staticmethod
    def _set_color(cr, color, alpha=1.0):
        cr.set_source_rgba(*color, alpha)

    def _draw_beveled_rect(self, cr, x, y, w, h, cut=None):
        """Draw a rectangle with 45-degree cut corners."""
        if cut is None:
            cut = self.CORNER_CUT
        cr.new_path()
        cr.move_to(x + cut, y)
        cr.line_to(x + w - cut, y)
        cr.line_to(x + w, y + cut)
        cr.line_to(x + w, y + h - cut)
        cr.line_to(x + w - cut, y + h)
        cr.line_to(x + cut, y + h)
        cr.line_to(x, y + h - cut)
        cr.line_to(x, y + cut)
        cr.close_path()

    def _draw_scanlines(self, cr, w, h):
        """Draw horizontal scanline overlay."""
        self._set_color(cr, (0, 0, 0), 0.03)
        for sy in range(0, h, 3):
            cr.rectangle(0, sy, w, 1)
        cr.fill()

    def _draw_glow_frame(self, cr, x, y, w, h):
        """Draw beveled frame with 3-layer glow."""
        for i, alpha in enumerate([0.06, 0.12, 0.25]):
            offset = 3 - i
            self._draw_beveled_rect(cr, x - offset, y - offset,
                                    w + 2 * offset, h + 2 * offset)
            self._set_color(cr, COLORS["accent"], alpha)
            cr.set_line_width(2)
            cr.stroke()

        # main border
        self._draw_beveled_rect(cr, x, y, w, h)
        self._set_color(cr, COLORS["accent"], 0.7)
        cr.set_line_width(1.5)
        cr.stroke()

    def _draw_diamond(self, cr, cx, cy, size=4):
        """Draw a small diamond shape."""
        cr.new_path()
        cr.move_to(cx, cy - size)
        cr.line_to(cx + size, cy)
        cr.line_to(cx, cy + size)
        cr.line_to(cx - size, cy)
        cr.close_path()
        cr.fill()

    def _draw_pcb_divider(self, cr, x, y, w):
        """Draw a PCB-trace style divider line."""
        self._set_color(cr, COLORS["accent"], 0.25)
        cr.set_line_width(1)
        mid = w / 2
        # left trace
        cr.move_to(x + 10, y)
        cr.line_to(x + mid - 20, y)
        cr.line_to(x + mid - 14, y - 4)
        cr.line_to(x + mid + 14, y - 4)
        cr.line_to(x + mid + 20, y)
        cr.line_to(x + w - 10, y)
        cr.stroke()

    def _draw_dot(self, cr, cx, cy, status, radius=4):
        """Draw a colored status dot with glow."""
        color = STATUS_COLORS.get(status, COLORS["accent"])
        # glow
        self._set_color(cr, color, 0.2)
        cr.arc(cx, cy, radius + 3, 0, 2 * math.pi)
        cr.fill()
        # dot
        self._set_color(cr, color, 0.9)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.fill()

    def _draw_progress_bar(self, cr, x, y, w, h, pct, color):
        """Draw a progress bar."""
        # background
        self._set_color(cr, COLORS["bg_dark"], 0.8)
        cr.rectangle(x, y, w, h)
        cr.fill()
        # border
        self._set_color(cr, COLORS["accent"], 0.3)
        cr.set_line_width(1)
        cr.rectangle(x, y, w, h)
        cr.stroke()
        # fill
        fill_w = w * (pct / 100)
        self._set_color(cr, color, 0.7)
        cr.rectangle(x, y, fill_w, h)
        cr.fill()
        # sheen
        self._set_color(cr, color, 0.15)
        cr.rectangle(x, y, fill_w, h / 2)
        cr.fill()

    # -- main draw --------------------------------------------------------

    def draw(self, cr, checks: List[SecurityCheck], score: int, scan_time: str):
        """Main draw entry point."""
        w = self.width
        h = self.height

        # clear
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # background fill inside bevel
        self._draw_beveled_rect(cr, 2, 2, w - 4, h - 4)
        self._set_color(cr, COLORS["bg_dark"], 0.92)
        cr.fill()

        # inner panel
        self._draw_beveled_rect(cr, 6, 6, w - 12, h - 12, cut=self.CORNER_CUT - 4)
        self._set_color(cr, COLORS["bg_panel"], 0.6)
        cr.fill()

        # glow frame
        self._draw_glow_frame(cr, 2, 2, w - 4, h - 4)

        # scanlines
        cr.save()
        self._draw_beveled_rect(cr, 2, 2, w - 4, h - 4)
        cr.clip()
        self._draw_scanlines(cr, w, h)
        cr.restore()

        # --- content ---
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        pad = self.PADDING
        y = pad

        # header: HowsMyPrivacy
        cr.set_font_size(self.HEADER_FONT_SIZE)
        self._set_color(cr, COLORS["accent"], 0.9)
        text = "HOWSMYPRIVACY"
        extents = cr.text_extents(text)
        tx = (w - extents.width) / 2
        y += 18
        cr.move_to(tx, y)
        cr.show_text(text)

        # decorative line + diamonds
        y += 8
        self._set_color(cr, COLORS["accent"], 0.4)
        cr.set_line_width(1)
        cr.move_to(pad + 10, y)
        cr.line_to(w / 2 - 12, y)
        cr.stroke()
        cr.move_to(w / 2 + 12, y)
        cr.line_to(w - pad - 10, y)
        cr.stroke()
        self._set_color(cr, COLORS["accent"], 0.6)
        self._draw_diamond(cr, w / 2, y, 5)

        y += 12

        # --- score ---
        score_color = COLORS["green"]
        if score < 70:
            score_color = COLORS["yellow"]
        if score < 40:
            score_color = COLORS["red"]

        cr.set_font_size(self.SCORE_FONT_SIZE)
        self._set_color(cr, score_color, 0.95)
        score_text = str(score)
        extents = cr.text_extents(score_text)
        sx = (w - extents.width) / 2
        y += 42
        cr.move_to(sx, y)
        cr.show_text(score_text)

        # score label
        y += 4
        cr.set_font_size(9)
        self._set_color(cr, COLORS["dim"], 0.8)
        label = "SECURITY SCORE"
        extents = cr.text_extents(label)
        cr.move_to((w - extents.width) / 2, y + 12)
        cr.show_text(label)
        y += 16

        # progress bar
        y += 6
        bar_x = pad + 20
        bar_w = w - 2 * pad - 40
        self._draw_progress_bar(cr, bar_x, y, bar_w, 8, score, score_color)
        y += 18

        # --- checks by section ---
        cr.set_font_size(self.BODY_FONT_SIZE)
        sections_seen = set()
        content_width = w - 2 * pad

        for check in checks:
            if check.section not in sections_seen:
                sections_seen.add(check.section)
                y += 8
                self._draw_pcb_divider(cr, pad, y, content_width)
                y += 14
                # section label
                cr.set_font_size(10)
                self._set_color(cr, COLORS["accent"], 0.6)
                section_label = f"// {check.section.upper()}"
                cr.move_to(pad + 8, y)
                cr.show_text(section_label)
                y += 10
                cr.set_font_size(self.BODY_FONT_SIZE)

            # draw check item
            dot_x = pad + 10
            dot_y = y + 6
            self._draw_dot(cr, dot_x, dot_y, check.status, radius=3.5)

            # name
            name_x = dot_x + 12
            self._set_color(cr, COLORS["text"], 0.9)
            cr.move_to(name_x, y + 10)
            cr.show_text(check.name)

            # detail (right-aligned with dot fill)
            detail = check.detail
            extents = cr.text_extents(detail)
            max_detail_w = w - pad - 8
            detail_x = max_detail_w - extents.width

            # dot fill between name and detail
            name_ext = cr.text_extents(check.name)
            fill_start = name_x + name_ext.width + 6
            fill_end = detail_x - 6
            if fill_end > fill_start + 10:
                self._set_color(cr, COLORS["dim"], 0.3)
                dots = ""
                dot_ext = cr.text_extents(".")
                ndots = int((fill_end - fill_start) / (dot_ext.width + 1.5))
                dots = " ".join(["." for _ in range(min(ndots, 30))])
                cr.move_to(fill_start, y + 10)
                cr.show_text(dots)

            # detail text
            detail_color = STATUS_COLORS.get(check.status, COLORS["text"])
            self._set_color(cr, detail_color, 0.8)
            cr.move_to(detail_x, y + 10)
            cr.show_text(detail)

            y += self.LINE_HEIGHT

        # --- footer ---
        y += 10
        self._set_color(cr, COLORS["accent"], 0.2)
        cr.set_line_width(1)
        cr.move_to(pad + 20, y)
        cr.line_to(w - pad - 20, y)
        cr.stroke()

        y += 14
        cr.set_font_size(9)
        self._set_color(cr, COLORS["dim"], 0.7)
        ts_text = f"LAST SCAN: {scan_time}" if scan_time else "SCANNING..."
        extents = cr.text_extents(ts_text)
        cr.move_to((w - extents.width) / 2, y)
        cr.show_text(ts_text)


# ---------------------------------------------------------------------------
# GTK4 Window
# ---------------------------------------------------------------------------

class SecHudWindow(Gtk.ApplicationWindow):
    """Main HUD window - frameless, transparent, moveable."""

    WIDTH = 300

    def __init__(self, app):
        super().__init__(application=app, title="HowsMyPrivacy - Desktop Monitor")

        self.scanner = SecurityScanner()
        self.frame = CyberpunkFrame()

        # window properties
        self.set_decorated(False)

        # sizing
        self.set_default_size(self.WIDTH, 600)

        # Create drawing area
        self.darea = Gtk.DrawingArea()
        self.darea.set_draw_func(self._on_draw)
        self.set_child(self.darea)

        # Add gesture controllers for mouse events
        # Right-click to quit
        right_click = Gtk.GestureClick.new()
        right_click.set_button(3)  # Right mouse button
        right_click.connect("pressed", self._on_right_click)
        self.add_controller(right_click)

        # Left-click to drag - simpler approach
        left_click = Gtk.GestureClick.new()
        left_click.set_button(1)
        left_click.connect("pressed", self._on_left_click)
        self.add_controller(left_click)

        # initial scan
        self._run_scan()

        # auto-refresh
        GLib.timeout_add_seconds(60, self._on_refresh)

    def _on_right_click(self, gesture, n_press, x, y):
        """Right-click to quit."""
        self.get_application().quit()

    def _on_left_click(self, gesture, n_press, x, y):
        """Left-click to begin window drag."""
        # GTK4/GDK4 way to begin interactive move
        native = self.get_native()
        if native:
            surface = native.get_surface()
            if surface:
                device = gesture.get_device()
                event = gesture.get_current_event()
                if event and hasattr(surface, 'begin_move'):
                    # Get root coordinates
                    root_x, root_y = event.get_root_coords() if hasattr(event, 'get_root_coords') else (x, y)
                    try:
                        surface.begin_move(device, 1, root_x, root_y, event.get_time())
                    except:
                        # Fallback - some compositors don't support this
                        print("Window dragging not supported by compositor")

    def _on_draw(self, area, cr, width, height, user_data=None):
        """Draw callback for GTK4."""
        self.frame.draw(cr, self.scanner.checks, self.scanner.score, self.scanner.scan_time)

    def _on_refresh(self):
        """Refresh timer callback."""
        self._run_scan()
        return True  # keep timer alive

    def _run_scan(self):
        """Run local checks immediately, then network checks in background."""
        self.scanner.checks = self.scanner.run_local_checks()
        self.scanner.score = self.scanner.calculate_score()
        self.scanner.scan_time = time.strftime("%H:%M:%S")
        self._update_size()
        self.darea.queue_draw()

        # network checks in background thread
        thread = threading.Thread(target=self._run_network_thread, daemon=True)
        thread.start()

    def _run_network_thread(self):
        """Background network checks."""
        net_checks = self.scanner.run_network_checks()
        GLib.idle_add(self._merge_network_checks, net_checks)

    def _merge_network_checks(self, net_checks):
        """Merge network check results."""
        # find insertion point after last network check
        insert_idx = 0
        for i, c in enumerate(self.scanner.checks):
            if c.section == "Network":
                insert_idx = i + 1
        for nc in net_checks:
            self.scanner.checks.insert(insert_idx, nc)
            insert_idx += 1
        self.scanner.score = self.scanner.calculate_score()
        self._update_size()
        self.darea.queue_draw()
        return False  # remove idle callback

    def _update_size(self):
        """Update window size based on content."""
        h = self.frame.measure_height(self.scanner.checks)
        self.set_default_size(self.WIDTH, h)
        self.darea.set_size_request(self.WIDTH, h)


# ---------------------------------------------------------------------------
# Application & Entry point
# ---------------------------------------------------------------------------

class HowsMyPrivacyApp(Gtk.Application):
    """GTK4 Application wrapper."""

    def __init__(self):
        super().__init__(application_id="org.howsmyprivacy.desktop")

    def do_activate(self):
        """Activated - create window."""
        win = SecHudWindow(self)
        win.present()


def main():
    app = HowsMyPrivacyApp()
    app.run(None)


if __name__ == "__main__":
    main()