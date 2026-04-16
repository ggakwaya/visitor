# Stealth Visitor

A Proxmox-optimized 24/7 orchestrator for simulating authentic website visits using NordVPN rotation and Playwright stealth.

## Features

- **Human-like behavior** — Bézier-curve mouse movement, idle jitter, variable-speed scrolling, weighted watch duration distribution (8s–10min)
- **Coherent fingerprints** — 15 hardcoded persona profiles with matching UA/viewport/platform/scale-factor (no contradictions)
- **Geo-matched sessions** — Browser timezone and locale automatically match the VPN exit country
- **Referrer simulation** — Weighted traffic sources (Google, YouTube, Reddit, direct, etc.)
- **Organic navigation** — 40% chance of visiting the YouTube homepage before the target video
- **Session reuse** — 30% chance of saving/loading browser state to simulate returning visitors
- **Cookie consent handling** — Automatically clicks through GDPR/YouTube consent dialogs
- **VPN rotation** — Weighted geographic selection (heavily NA: Canada/USA) via NordVPN
- **UA staleness tracking** — Run `python personas.py` to check if embedded user-agent strings need updating

## Project Structure

```
visitor/
├── visitor.py       # Orchestrator: VPN rotation, visit loop, stats
├── behavior.py      # Human simulation: mouse, scroll, watch, consent
├── personas.py      # Coherent browser fingerprint profiles + staleness checker
├── config.yaml      # Targets, VPN locations, referrers, session settings
├── requirements.txt # Python dependencies
├── setup_lxc.sh     # Proxmox LXC provisioning script
└── stats.json       # Visit progress tracking (auto-generated)
```

## Installation (Inside Proxmox LXC)

1. Clone the repo
2. Run `chmod +x setup_lxc.sh && ./setup_lxc.sh`
3. Login to NordVPN: `nordvpn login --token <TOKEN>`

## Usage

### Production (24/7 with VPN rotation)

```bash
python visitor.py
```

Targets and goals are configured in `config.yaml`. The script runs in a loop until all goals are met.

### Testing (Local without VPN)

```bash
# Headless — runs one visit per target
python visitor.py --no-vpn

# Visible browser — watch the mouse movement and interactions
python visitor.py --no-vpn --visible
```

### Check UA Freshness

```bash
python personas.py
```

This reports whether the embedded Chrome/Firefox user-agent strings are stale and need a manual update (recommended every ~6 weeks).

## Configuration

All settings are in [`config.yaml`](config.yaml):

| Section | What it controls |
|---------|-----------------|
| `targets` | URLs to visit and their goal visit counts |
| `locations` | VPN exit countries with weights, timezones, and locales |
| `browsers` | Browser engine weights (chromium vs firefox) |
| `referrers` | Weighted referrer URLs to simulate traffic sources |
| `jitter` | Min/max delay between visits (seconds) |
| `session_reuse_probability` | Chance of saving/loading browser state (0.0–1.0) |

## Safe Testing

> **⚠️ Do NOT test against channels you care about.**

1. Create a throwaway Google account (use VPN + temporary email)
2. Upload a short **unlisted** video to a throwaway channel
3. Use that unlisted URL as your test target in `config.yaml`
4. Monitor YouTube Studio analytics on the throwaway to verify views are counted
