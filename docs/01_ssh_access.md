# SSH Access

Thyra runs an SSH server on port 22. Authentication uses SSH keys (no password prompt once keys are set up).

## Credentials

| Field | Value |
|---|---|
| User | `thyra` |
| Password (fallback) | `Metalcore1!` |
| VNC Password | `Metalcore1!` |

## Connection Methods (in priority order)

### 1. Tailscale (preferred — works from anywhere)
```bash
ssh thyra@orin-nano
```
Tailscale gives `orin-nano` a stable address regardless of network. Works over WiFi, Ethernet, phone hotspot, 4G — no config changes needed.

### 2. USB-C Gadget (when cabled to laptop)
```bash
ssh thyra@192.168.55.1
```
The Jetson creates a virtual Ethernet interface over USB-C. IP is always `192.168.55.1`. Only works when connected via USB-C to a machine.

### 3. Local Network IP
```bash
ssh thyra@<local-ip>
```
Find the IP with `thyra status` or check your router's DHCP table. Changes when moving networks.

---

## Parrot Laptop — One-Word Shortcut

The `~/.ssh/config` is pre-configured:
```bash
ssh thyra        # USB-C connection (192.168.55.1)
ssh thyra-ts     # Tailscale connection (orin-nano)
```

---

## Termux (Android) Setup

Run these once in Termux:

```bash
# Install SSH
pkg install openssh

# Generate a key
ssh-keygen -t ed25519 -C "termux-phone"

# Copy your public key — paste it into the Jetson:
cat ~/.ssh/id_ed25519.pub
# Then on Jetson (or via another SSH session):
# echo "PASTE_KEY_HERE" >> ~/.ssh/authorized_keys

# Connect via Tailscale
ssh thyra@orin-nano

# Or USB-C
ssh thyra@192.168.55.1
```

To install Tailscale on Android: install the **Tailscale** app from Google Play, sign in with the same account used to authorize the Jetson.

---

## Adding Keys from Any New Machine

```bash
# On the new machine, get your public key:
cat ~/.ssh/id_ed25519.pub    # or id_rsa.pub

# Append it to Jetson authorized_keys (one-time):
ssh thyra@orin-nano "echo 'PASTE_KEY' >> ~/.ssh/authorized_keys"
```

---

## Troubleshooting SSH

| Problem | Fix |
|---|---|
| `Permission denied (publickey)` | Your key isn't in `~/.ssh/authorized_keys`. Use password auth once to add it. |
| `Connection refused` | SSH service down. Boot Jetson and wait 30s. |
| `Connection timed out` | Not on same network and Tailscale isn't connected. Check `tailscale status`. |
| USB-C not getting 192.168.55.1 | USB gadget interface may not have loaded. Try `sudo modprobe g_ether` on Jetson. |
| `Host key changed` warning | Run `ssh-keygen -R 192.168.55.1` on the client then reconnect. |
