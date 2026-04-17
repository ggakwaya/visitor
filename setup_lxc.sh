#!/bin/bash
set -e

echo "--- Installing System Dependencies ---"
apt-get update
apt-get install -y python3-pip python3-venv curl wget

echo "--- Installing NordVPN CLI ---"
sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh) || true

echo "--- Setting up Python Environment ---"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "--- Installing Playwright Browsers and System Deps ---"
# This installs the browser binaries (both chromium and firefox)
venv/bin/python3 -m playwright install chromium firefox
# This installs the required system libraries (GTK, GStreamer, etc.)
venv/bin/python3 -m playwright install-deps

echo "--- SUCCESS ---"
echo "Next steps:"
echo "1. nordvpn login --token <YOUR_TOKEN>"
echo "2. source venv/bin/activate"
echo "3. python visitor.py 'https://your-target.com'"
