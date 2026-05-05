"""
Thyra WAN Command Vocabulary
Maps plain English commands to structured intent objects.
"""

COMMANDS = {
    # ── OSINT ──────────────────────────────────────────────────────────────
    "recon_ng": {
        "aliases": ["recon-ng", "reconng", "recon ng", "full osint", "osint chain"],
        "args": ["target"],
        "model": "instruct",
        "description": "Multi-source OSINT chain via recon-ng (domains, hosts, contacts)",
        "workflow": "recon_ng",
    },
    "recon": {
        "aliases": ["recon", "reconnaissance", "gather info on", "info on", "look up",
                    "osint", "intel on", "investigate", "profile"],
        "args": ["target"],
        "model": "instruct",
        "description": "Full passive OSINT profile on a domain, IP, or person",
        "workflow": "osint_full",
    },
    "email_harvest": {
        "aliases": ["email harvest", "find emails", "harvest emails for", "emails from"],
        "args": ["domain"],
        "model": "instruct",
        "description": "Harvest email addresses associated with a domain",
        "workflow": "email_harvest",
    },
    "subdomain_scan": {
        "aliases": ["subdomain scan", "subdomains", "enumerate subdomains", "find subdomains",
                    "subdomain enum", "enum subdomains", "sub enum", "sub scan", "brute subdomains"],
        "args": ["domain"],
        "model": "code",
        "description": "Enumerate subdomains of a target domain",
        "workflow": "subdomain_scan",
    },
    "dns_recon": {
        "aliases": ["dns recon", "dns lookup", "dns records", "check dns"],
        "args": ["domain"],
        "model": "code",
        "description": "Full DNS record enumeration",
        "workflow": "dns_recon",
    },
    "whois": {
        "aliases": ["whois", "who owns", "domain info", "registrar"],
        "args": ["target"],
        "model": "code",
        "description": "WHOIS registration data for domain or IP",
        "workflow": "whois",
    },

    # ── NETWORK ────────────────────────────────────────────────────────────
    "port_scan": {
        "aliases": ["port scan", "scan ports", "open ports", "nmap"],
        "args": ["target"],
        "model": "code",
        "description": "TCP port scan and service detection",
        "workflow": "port_scan",
    },
    "service_scan": {
        "aliases": ["service scan", "what services", "detect services", "banner grab"],
        "args": ["target"],
        "model": "code",
        "description": "Service version detection on open ports",
        "workflow": "service_scan",
    },
    "vuln_scan": {
        "aliases": ["vuln scan", "vulnerability scan", "check vulns", "scan for vulns"],
        "args": ["target"],
        "model": "instruct",
        "description": "Vulnerability scan with nmap NSE scripts",
        "workflow": "vuln_scan",
    },
    "ping_sweep": {
        "aliases": ["ping sweep", "discover hosts", "live hosts", "who is up", "host discovery"],
        "args": ["subnet"],
        "model": "code",
        "description": "Discover live hosts on a subnet",
        "workflow": "ping_sweep",
    },
    "traceroute": {
        "aliases": ["traceroute", "trace route", "path to", "hops to"],
        "args": ["target"],
        "model": "code",
        "description": "Network path trace to target",
        "workflow": "traceroute",
    },
    "packet_capture": {
        "aliases": ["capture packets", "sniff", "capture traffic", "pcap", "tshark",
                    "sniff traffic", "monitor traffic", "capture", "listen on", "dump traffic"],
        "args": ["interface", "filter?", "duration?"],
        "model": "code",
        "description": "Packet capture with optional BPF filter",
        "workflow": "packet_capture",
    },

    # ── WIFI ───────────────────────────────────────────────────────────────
    "kismet_survey": {
        "aliases": ["kismet survey", "kismet scan", "passive wifi", "wifi passive", "silent wifi scan"],
        "args": ["interface?"],
        "model": "code",
        "description": "Passive 802.11 survey via Kismet REST API (no probe frames)",
        "workflow": "kismet_survey",
    },
    "wifi_survey": {
        "aliases": ["wifi survey", "scan wifi", "find networks", "list access points", "ap scan"],
        "args": [],
        "model": "code",
        "description": "Scan for nearby 802.11 access points (requires Alfa adapter)",
        "workflow": "wifi_survey",
    },
    "wifi_clients": {
        "aliases": ["wifi clients", "clients on", "connected devices", "find clients"],
        "args": ["bssid?"],
        "model": "code",
        "description": "Discover clients associated with APs",
        "workflow": "wifi_clients",
    },
    "handshake_capture": {
        "aliases": ["capture handshake", "grab handshake", "handshake", "wpa capture"],
        "args": ["bssid", "channel"],
        "model": "instruct",
        "description": "Capture WPA/WPA2 4-way handshake for offline analysis",
        "workflow": "handshake_capture",
    },

    # ── SDR / RF ───────────────────────────────────────────────────────────
    "rtl_power_scan": {
        "aliases": ["rtl power", "power scan", "signal survey", "power spectrum", "spectrum power"],
        "args": ["freq_range?"],
        "model": "code",
        "description": "RTL-SDR power scan → JSON with top signals above threshold",
        "workflow": "rtl_power_scan",
    },
    "hackrf_scan": {
        "aliases": ["hackrf scan", "hackrf sweep", "hackrf receive", "hackrf listen",
                    "hackrf capture", "hackrf python"],
        "args": ["start_freq?", "end_freq?"],
        "model": "code",
        "description": "HackRF One sweep via python_hackrf library",
        "workflow": "spectrum_scan",
    },
    "spectrum_scan": {
        "aliases": ["spectrum scan", "scan spectrum", "rf scan", "scan rf", "scan frequencies",
                    "rf sweep", "sweep rf", "frequency sweep", "sweep frequencies",
                    "sweep spectrum", "freq sweep"],
        "args": ["start_freq?", "end_freq?"],
        "model": "code",
        "description": "Wideband RF spectrum scan (HackRF CLI or RTL-SDR)",
        "workflow": "spectrum_scan",
    },
    "fm_scan": {
        "aliases": ["fm scan", "scan fm", "find fm stations", "fm stations"],
        "args": [],
        "model": "code",
        "description": "Scan FM broadcast band 87–108 MHz",
        "workflow": "fm_scan",
    },
    "aircraft_scan": {
        "aliases": ["aircraft scan", "ads-b", "planes", "air traffic", "adsb"],
        "args": [],
        "model": "code",
        "description": "ADS-B aircraft position decoding on 1090 MHz",
        "workflow": "aircraft_scan",
    },
    "iot433": {
        "aliases": ["433 scan", "iot scan", "scan 433", "sensor scan", "find sensors"],
        "args": [],
        "model": "code",
        "description": "Decode 433MHz IoT sensor transmissions (weather, remotes, etc.)",
        "workflow": "iot433",
    },
    "lora_scan": {
        "aliases": ["lora scan", "scan lora", "lora traffic", "meshtastic scan"],
        "args": ["frequency?"],
        "model": "code",
        "description": "Monitor LoRa / Meshtastic transmissions",
        "workflow": "lora_scan",
    },

    # ── WEB ────────────────────────────────────────────────────────────────
    "web_scan": {
        "aliases": ["web scan", "scan website", "http scan", "check website"],
        "args": ["url"],
        "model": "instruct",
        "description": "Web vulnerability scan with nikto + httpx",
        "workflow": "web_scan",
    },
    "dir_fuzz": {
        "aliases": ["dir fuzz", "fuzz dirs", "directory scan", "find dirs", "gobuster"],
        "args": ["url"],
        "model": "code",
        "description": "Directory/file enumeration with ffuf or gobuster",
        "workflow": "dir_fuzz",
    },

    # ── ESP32 (PinPulse Shield) ────────────────────────────────────────────
    "esp32_scan": {
        "aliases": ["esp32 scan", "esp32 wifi scan", "pinpulse scan", "wifi scan esp32"],
        "args": [],
        "model": "code",
        "description": "WiFi AP scan via ESP32 PinPulse (USB serial, JSON output)",
        "workflow": "esp32_scan",
    },
    "esp32_deauth": {
        "aliases": ["esp32 deauth", "deauth esp32", "pinpulse deauth", "esp deauth"],
        "args": ["bssid", "channel"],
        "model": "code",
        "description": "Send deauth frames via ESP32 PinPulse to target AP",
        "workflow": "esp32_deauth",
    },
    "esp32_ble": {
        "aliases": ["ble scan", "scan ble", "bluetooth scan", "find bluetooth", "esp32 ble"],
        "args": ["seconds?"],
        "model": "code",
        "description": "Scan BLE devices via ESP32 PinPulse",
        "workflow": "esp32_ble",
    },

    # ── COMPOUND WORKFLOWS ─────────────────────────────────────────────────
    "full_recon": {
        "aliases": ["full recon", "deep recon", "everything on", "full profile"],
        "args": ["target"],
        "model": "instruct",
        "description": "Full chain: whois → dns → subdomain → port scan → web scan",
        "workflow": "full_recon",
    },
    "network_map": {
        "aliases": ["network map", "map network", "map the network", "network overview"],
        "args": ["subnet?"],
        "model": "instruct",
        "description": "Discover and fingerprint all hosts on local network",
        "workflow": "network_map",
    },
    "rf_survey": {
        "aliases": ["rf survey", "rf overview", "scan all rf", "rf environment",
                    "full rf", "rf recon", "radio survey", "radio environment"],
        "args": [],
        "model": "instruct",
        "description": "Full RF environment survey: spectrum + 433 + aircraft + LoRa",
        "workflow": "rf_survey",
    },
}


def match_command(text: str) -> tuple[str | None, dict | None]:
    """Match plain English input to a command entry, preferring longer alias matches."""
    text_lower = text.lower().strip()
    best_cmd = None
    best_alias_len = 0
    for cmd_name, cmd in COMMANDS.items():
        for alias in cmd["aliases"]:
            if (text_lower.startswith(alias) or alias in text_lower) and len(alias) > best_alias_len:
                best_cmd = (cmd_name, cmd)
                best_alias_len = len(alias)
    return best_cmd if best_cmd else (None, None)


def list_commands() -> str:
    lines = []
    category = None
    categories = {
        "OSINT":    ["recon_ng", "recon", "email_harvest", "subdomain_scan", "dns_recon", "whois"],
        "NETWORK":  ["port_scan", "service_scan", "vuln_scan", "ping_sweep", "traceroute", "packet_capture"],
        "WIFI":     ["kismet_survey", "wifi_survey", "wifi_clients", "handshake_capture"],
        "SDR/RF":   ["rtl_power_scan", "hackrf_scan", "spectrum_scan", "fm_scan", "aircraft_scan", "iot433", "lora_scan"],
        "ESP32":    ["esp32_scan", "esp32_deauth", "esp32_ble"],
        "WEB":      ["web_scan", "dir_fuzz"],
        "COMPOUND": ["full_recon", "network_map", "rf_survey"],
    }
    for cat, cmds in categories.items():
        lines.append(f"\n  [{cat}]")
        for name in cmds:
            cmd = COMMANDS[name]
            primary = cmd["aliases"][0]
            args = " ".join(f"<{a}>" for a in cmd["args"] if not a.endswith("?"))
            opt_args = " ".join(f"[{a[:-1]}]" for a in cmd["args"] if a.endswith("?"))
            sig = f"  {primary} {args} {opt_args}".rstrip()
            lines.append(f"    {sig:<40} {cmd['description']}")
    return "\n".join(lines)
