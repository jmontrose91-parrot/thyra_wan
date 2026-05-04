# Thyra Agent — Usage Guide

Thyra is a plain-English SIGINT/OSINT agent. Type what you want in natural language and it generates exact CLI commands, runs them, and reports findings.

## Starting the Agent

```bash
# SSH in
ssh thyra@orin-nano

# Check status
thyra status

# Start LLM server (if not running)
thyra server

# Launch interactive REPL
thyra
```

---

## Plain English Commands

Type commands directly — no flags, no syntax to remember:

```
thyra> port scan 192.168.1.1
thyra> scan wifi
thyra> recon example.com
thyra> dns recon target.org
thyra> hackrf sweep 100 500
thyra> 433 scan
thyra> ads-b
thyra> lora scan
thyra> help
```

---

## Command Categories

### OSINT
| Command | What it does |
|---|---|
| `recon <target>` | Full passive OSINT: whois → DNS → subdomains → emails → Shodan |
| `recon-ng <domain>` | Multi-source chain via recon-ng (hosts, contacts, IPs) |
| `whois <target>` | Domain registration info |
| `dns recon <domain>` | All DNS records (A, MX, NS, TXT, AXFR attempt) |
| `subdomain scan <domain>` | Enumerate subdomains with dnsrecon + gobuster |
| `email harvest <domain>` | Harvest email addresses from public sources |

### Network
| Command | What it does |
|---|---|
| `port scan <target>` | TCP SYN scan + service detection |
| `service scan <target>` | Full service fingerprinting with NSE scripts |
| `vuln scan <target>` | nmap NSE vuln scripts → CVE detection |
| `ping sweep <subnet>` | Discover live hosts (e.g. `ping sweep 192.168.1.0/24`) |
| `traceroute <target>` | Network path + hop count |
| `capture packets <iface>` | tshark packet capture with optional BPF filter |

### WiFi
| Command | What it does |
|---|---|
| `scan wifi` | airodump-ng AP survey (requires Alfa adapter in wlan0) |
| `kismet survey` | Passive AP survey via Kismet REST API (no probe frames) |
| `wifi clients` | Discover associated clients |
| `capture handshake <bssid> <ch>` | WPA/WPA2 4-way handshake capture for offline analysis |

### SDR / RF
| Command | What it does |
|---|---|
| `433 scan` | Decode 433MHz IoT: weather stations, key fobs, sensors |
| `aircraft scan` | ADS-B aircraft positions on 1090 MHz via dump1090 |
| `lora scan` | Meshtastic/LoRa mesh packet capture via serial |
| `fm scan` | FM broadcast band 87–108 MHz power scan |
| `hackrf sweep <start> <end>` | HackRF One wideband sweep (MHz) |
| `spectrum scan <start> <end>` | RTL-SDR power scan → top signals |
| `power scan <range>` | rtl_power JSON output with signal threshold filter |

### Web
| Command | What it does |
|---|---|
| `web scan <url>` | nikto + httpx + nuclei vulnerability scan |
| `dir fuzz <url>` | ffuf + gobuster directory/file enumeration |

### Compound
| Command | What it does |
|---|---|
| `full recon <target>` | Chain: whois → dns → subdomain → ports → web |
| `network map <subnet>` | Full subnet discovery + fingerprinting |
| `rf survey` | Full RF sweep: spectrum + 433 + aircraft + LoRa |

---

## Subcommands

```bash
thyra status          # GPU, models, services, ports, hardware
thyra smoke           # Full self-test (61 checks)
thyra server          # Start/wait for llama-server
thyra test            # GPU inference benchmark
thyra findings        # Browse scan results DB
thyra findings --last 10        # Last 10 findings
thyra findings --target 192.168.1.1  # Filter by target
thyra findings --detail <id>    # Full output for one finding
thyra agent <task>    # Run ReAct agent loop on a task
```

---

## Output

- JSON findings saved to `/tmp/thyra_output/`
- All results logged to SQLite at `~/findings.db`
- Log file at `~/logs/thyra.log` (rotating, 10MB max)
- Browse with `thyra findings`

---

## LLM Server

The LLM server runs as a systemd service:
```bash
sudo systemctl status thyra-llama    # check
sudo systemctl restart thyra-llama   # restart
thyra server                         # wait for it to come up
```

Two models — swapped by task type:
- **Qwen3-8B-abliterated** — reasoning, ReAct loops, analysis
- **Qwen2.5-Coder-7B-abliterated** — exact CLI command generation
