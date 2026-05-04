# Tailscale — Network-Agnostic Access

Tailscale gives every device a stable private IP and DNS name that works from any network — home WiFi, office, coffee shop, 4G, phone hotspot. No port forwarding, no dynamic DNS, no VPN config files.

## One-Time Setup

### Step 1: Authorize the Jetson (done once)

After `tailscale up` runs on the Jetson, visit the auth URL it prints:
```
https://login.tailscale.com/a/XXXXXXXX
```
Sign in with your Tailscale account. The Jetson joins your tailnet as `orin-nano`.

### Step 2: Install Tailscale on your other devices

| Device | Install |
|---|---|
| Parrot Linux | `curl -fsSL https://tailscale.com/install.sh \| sh && sudo tailscale up` |
| Android | Install **Tailscale** from Google Play, sign in |
| iOS | Install **Tailscale** from App Store, sign in |
| Windows/macOS | Download from tailscale.com/download |

Sign in to the **same Tailscale account** on all devices. They all join the same network.

---

## Usage

Once all devices are on the same tailnet:

```bash
# SSH from anywhere
ssh thyra@orin-nano

# VNC from anywhere
vncviewer orin-nano:5901

# Check Tailscale status on Jetson
ssh thyra@orin-nano "tailscale status"
```

The hostname `orin-nano` resolves to the Jetson's Tailscale IP (`100.x.x.x`) on all connected devices automatically.

---

## Status Commands (on Jetson)

```bash
tailscale status          # see all connected devices + IPs
tailscale ip              # show this device's Tailscale IP
tailscale ping orin-nano  # test connectivity
sudo systemctl status tailscaled   # check daemon
```

---

## Mobile Hotspot Scenario

When the Jetson is connected to your phone's hotspot:
1. Phone has Tailscale running (Android app)
2. Jetson has Tailscale running (systemd service)
3. Laptop has Tailscale running
→ All three can reach each other via `orin-nano` / tailscale IPs regardless of the hotspot NAT

The phone's hotspot acts as a regular network — Tailscale punches through the double-NAT automatically.

---

## Tailscale SSH (Optional)

Tailscale has a built-in SSH feature (`--ssh` flag used during setup):
```bash
# If Tailscale SSH is enabled, you can SSH without managing keys:
ssh thyra@orin-nano   # uses Tailscale identity instead of SSH keys
```

This is enabled on the Jetson. You can also use it as a fallback if your SSH key isn't loaded.

---

## Troubleshooting Tailscale

| Problem | Fix |
|---|---|
| `orin-nano` doesn't resolve | Run `tailscale status` on both devices — both must show as connected |
| Jetson not in tailnet after reboot | `ssh thyra "sudo systemctl restart tailscaled"` |
| Auth URL expired | Run `sudo tailscale up` again on Jetson — new URL generated |
| Slow connection | Tailscale may be relaying. Check with `tailscale ping orin-nano --c 5` — should eventually say "direct" |
