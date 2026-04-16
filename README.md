# Stealth Visitor

A Proxmox-optimized 24/7 orchestrator for simulating "as new as possible" website visits using NordVPN rotation and Playwright stealth.

## Features
- **VPN Rotation:** Weighted geographic selection (Heavily NA: Canada/USA).
- **Stealth Browsing:** Uses `playwright-stealth` to bypass bot detection.
- **Fingerprint Randomization:** Random User-Agents, Viewports, and Hardware scaling.
- **Persistent:** Designed to run 24/7 as a systemd service.

## Installation (Inside Proxmox LXC)
1. Clone the repo.
2. Run `chmod +x setup_lxc.sh && ./setup_lxc.sh`.
3. Login to NordVPN: `nordvpn login --token <TOKEN>`.

## Usage
### Production (24/7 with VPN rotation)
```bash
python visitor.py "https://target-url.com"
```

### Testing (Local without VPN)
```bash
python visitor.py "https://target-url.com" --no-vpn
```

## Configuration
Adjust weights and timing in `config.yaml`.
