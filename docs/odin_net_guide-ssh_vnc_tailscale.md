# odin_net_guide-ssh_vnc_tailscale

Offline reference. Save a copy on every device.
Last updated: 2026-05-04

---

## Devices & Addresses

| Device | Tailscale IP | Tailscale Name | USB/Local |
|---|---|---|---|
| Jetson Orin Nano | 100.99.170.24 | orin-nano | 192.168.55.1 (USB-C) |
| Parrot Laptop | 100.78.108.17 | parrot | — |
| Raspberry Pi | *(add when joined)* | *(add when joined)* | 192.168.x.x (check router) |
| Phone | *(your tailscale IP)* | *(your device name)* | — |

**Credentials:**
- SSH user: `thyra`
- SSH/VNC password: `Metalcore1!`
- VNC port: `5901`

---

## 1. SSH

### From Parrot Laptop
```bash
ssh thyra          # Tailscale (any network)
ssh thyra-usb      # USB-C cable only
ssh thyra@100.99.170.24   # by IP if hostname fails
```

### From Termux (Android)
```bash
pkg install openssh
ssh thyra@100.99.170.24
ssh thyra@orin-nano        # if MagicDNS is working
```

### From Any Machine
```bash
ssh thyra@100.99.170.24    # Tailscale IP — always works
ssh thyra@192.168.55.1     # USB-C cable only
ssh thyra@<local-ip>       # same WiFi/LAN only
```

### To a Raspberry Pi
```bash
ssh pi@<tailscale-ip>      # fill in from table above
ssh pi@raspberrypi.local   # same network only
```

### First-Time Key Setup (skip password prompts)
```bash
# On the new machine:
ssh-keygen -t ed25519      # generate key if needed
ssh-copy-id thyra@100.99.170.24   # authorize it on Jetson
# Enter password once: Metalcore1!
```

---

## 2. VNC

VNC gives you a full desktop. Password is `Metalcore1!` on all connections.

### From Parrot Laptop
```bash
vncviewer 100.99.170.24:5901     # Tailscale
vncviewer 192.168.55.1:5901      # USB-C
```

### From Android
Install **RealVNC Viewer** or **bVNC** from Google Play.
- Server: `100.99.170.24:5901`
- Password: `Metalcore1!`

### SSH Tunnel (if port 5901 is blocked on a network)
```bash
# Terminal 1 — open tunnel:
ssh -L 5901:localhost:5901 thyra@100.99.170.24

# Terminal 2 — connect through it:
vncviewer localhost:5901
```

---

## 3. Tailscale

Tailscale is the backbone. Every device on the same account can reach every other device regardless of what network each is on.

### Connect a New Device
1. Install Tailscale (tailscale.com/download or Google Play / App Store)
2. Sign in with account: `jmontrose91-parrot`
3. Toggle on — done. The device is now reachable by its Tailscale IP from all other devices.

### Check Who's Online
```bash
tailscale status          # see all connected devices
tailscale ping orin-nano  # test direct connectivity
tailscale ip              # show this device's Tailscale IP
```

### Android Troubleshooting
- App shows "Connected" but nothing reachable → toggle VPN off/on in app
- `err_name_not_resolved` → **disable "Always on VPN"** in Android Settings → Network → VPN, then force-stop and reopen Tailscale
- Still failing → reboot phone, reopen app
- Login page won't load → switch from WiFi to mobile data for login, switch back after

---

## 4. Same-Network (No Internet, No Tailscale)

When Tailscale is unavailable, use local IPs. All devices must be on the same WiFi/LAN or hotspot.

### Find Devices on the Network
```bash
# On Linux:
ip neighbor show                        # show ARP table
nmap -sn 192.168.1.0/24                # ping sweep your subnet
avahi-browse -a 2>/dev/null | head -20  # mDNS discovery

# From Android Termux:
nmap -sn 192.168.1.0/24
```

### Jetson via USB-C (no network needed at all)
Plug USB-C cable between Jetson and laptop. Jetson creates a virtual Ethernet:
```bash
ssh thyra@192.168.55.1    # always works when cabled
vncviewer 192.168.55.1:5901
```
No WiFi, no internet, no router required.

### Phone as Hotspot
1. Enable hotspot on phone
2. Connect Jetson (and other devices) to hotspot WiFi
3. Check hotspot's DHCP table for Jetson IP, or scan:
   ```bash
   # On Jetson (SSH in via USB-C first if needed):
   ip addr show   # find its IP on the hotspot network
   ```
4. Tailscale still works over hotspot — use Tailscale IPs as normal

### Raspberry Pi on Local Network
```bash
ping raspberrypi.local    # mDNS — works on same network without knowing IP
ssh pi@raspberrypi.local
```
If `.local` doesn't resolve: `nmap -sn <subnet>` to find it.

---

## 5. Quick Troubleshooting

### SSH: Connection refused
```bash
# Check SSH is running on the target:
ssh thyra@192.168.55.1   # try USB-C first
sudo systemctl status ssh
sudo systemctl start ssh
```

### SSH: Permission denied (publickey)
```bash
# Use password auth once to add your key:
ssh-copy-id thyra@100.99.170.24
# Password: Metalcore1!
```

### SSH: Host key changed warning
```bash
ssh-keygen -R 192.168.55.1    # clear old key
ssh-keygen -R 100.99.170.24
# Then reconnect normally
```

### VNC: Black screen
```bash
ssh thyra "DISPLAY=:1 openbox-session &"
# or restart VNC:
ssh thyra "sudo systemctl restart vncserver@thyra"
```

### VNC: Connection refused on 5901
```bash
ssh thyra "sudo systemctl restart vncserver@thyra"
ssh thyra "ss -tnlp | grep 5901"   # confirm it's listening
```

### Tailscale: Device not reachable
```bash
tailscale status             # is the target device showing as connected?
tailscale ping orin-nano     # test path — will say "direct" or "relayed"
sudo systemctl restart tailscaled   # restart daemon if stuck
```

### Tailscale: Slow / high latency
```bash
tailscale ping orin-nano --c 10
# If it says "relayed" instead of "direct", the two devices can't
# reach each other directly (double-NAT). Still works, just slower.
# Fix: make sure both devices have Tailscale running and are logged in.
```

### No Internet + No USB Cable
If you can't reach the Jetson at all:
1. Connect an HDMI monitor directly to the Jetson (DisplayPort adapter needed)
2. Or connect USB-C cable → `ssh thyra@192.168.55.1`
3. Check Jetson's network: `ip addr show` — find any active interface
4. Connect both devices to the same phone hotspot, scan for IP

---

## 6. Services on the Jetson (restart if broken)

```bash
sudo systemctl restart ssh                # SSH server
sudo systemctl restart vncserver@thyra    # VNC desktop
sudo systemctl restart tailscaled         # Tailscale
sudo systemctl restart thyra-llama        # LLM server (port 8080)

# Check all at once:
thyra status
```

---

## 7. Useful One-Liners

```bash
# What's my Tailscale IP?
tailscale ip

# What devices are on my tailnet?
tailscale status

# What's the local network subnet?
ip route | grep -v default | head -5

# Find all devices on local network:
nmap -sn $(ip route | grep -v default | awk 'NR==1{print $1}')

# Copy a file to Jetson:
scp myfile.txt thyra@100.99.170.24:~/

# Copy a file from Jetson:
scp thyra@100.99.170.24:~/agent/findings.db ./

# Forward a remote port to localhost (useful for web UIs):
ssh -L 8080:localhost:8080 thyra@100.99.170.24
# Then open http://localhost:8080 in your browser
```
