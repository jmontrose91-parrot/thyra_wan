# VNC Access

TigerVNC runs on port 5901 (display `:1`). The session has Openbox window manager and an xterm pre-loaded in `~/agent`.

## Credentials

| Field | Value |
|---|---|
| Host (Tailscale) | `orin-nano:5901` |
| Host (USB-C) | `192.168.55.1:5901` |
| Password | `Metalcore1!` |
| Resolution | 1280x800 |

---

## Connecting from Parrot Linux

```bash
# Install viewer if needed
sudo apt-get install tigervnc-viewer

# Connect via Tailscale
vncviewer orin-nano:5901

# Connect via USB-C
vncviewer 192.168.55.1:5901
```

Password: `Metalcore1!`

---

## Connecting from Android (Termux / Phone)

Install **RealVNC Viewer** or **bVNC** from Google Play.

- Server: `orin-nano:5901` (via Tailscale) or `192.168.55.1:5901` (USB-C)
- Password: `Metalcore1!`

With Tailscale running on your phone, `orin-nano` resolves directly — no IP address needed.

---

## Connecting from Any Other Machine

Any VNC client works:

| OS | Client | Install |
|---|---|---|
| Linux | `vncviewer` (TigerVNC) | `apt install tigervnc-viewer` |
| macOS | Screen Sharing (built-in) or TigerVNC | `brew install tiger-vnc` |
| Windows | TigerVNC, RealVNC | Download from tigervnc.org |
| Android | RealVNC Viewer, bVNC | Google Play |
| iOS | RealVNC Viewer | App Store |

---

## SSH Tunnel (if VNC port is blocked)

If port 5901 is blocked on a network, tunnel it over SSH:

```bash
# On your client machine:
ssh -L 5901:localhost:5901 thyra@orin-nano

# Then in another terminal:
vncviewer localhost:5901
```

---

## VNC Auto-Start

VNC starts automatically at boot via systemd:
```bash
sudo systemctl status vncserver@thyra    # check status
sudo systemctl restart vncserver@thyra   # restart if needed
```

---

## Troubleshooting VNC

| Problem | Fix |
|---|---|
| `Connection refused` on 5901 | `ssh thyra "sudo systemctl restart vncserver@thyra"` |
| Black/blank screen | WM crashed. SSH in and run `DISPLAY=:1 openbox-session &` |
| Wrong password | Password is `Metalcore1!`. Reset: `ssh thyra "vncpasswd"` |
| Slow/laggy | Normal over internet. Over LAN or USB-C it should be fast. |
| VNC session dies on reboot | Service should auto-start. Check: `systemctl is-enabled vncserver@thyra` |
