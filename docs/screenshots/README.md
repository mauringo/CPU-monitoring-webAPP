# Dashboard screenshots

Six full-page PNG screenshots cover the Overview, Devices and GPU/NPU pages
in both light and dark themes. Captured at a 1440-pixel browser width using
real telemetry from a Thundercomm RUBIK Pi 3. The Qualcomm NPU terminal was
running through the installed Snap in devmode. These are not Raspberry Pi 5
validation screenshots.

The screenshots render this repository's current static files, including the
Qualcomm NPU permission notice, against the running app's real API and nvtop
stream. No metrics are mocked or generated. Hardware identifiers and readings
reflect the capture machine and will differ on other systems.

## Regenerate

Start the dashboard on port 12121, then install the optional browser tooling
in a virtual environment:

```sh
python3 -m venv .venv-screenshots
. .venv-screenshots/bin/activate
pip install playwright
python -m playwright install chromium
python scripts/capture-screenshots.py
```

Chromium's system libraries must also be available. An alternate dashboard
origin can be supplied as the first argument to the script. The capture waits
for actual CPU history, completed hardware discovery and a live nvtop stream.
It fails if the terminal is unavailable rather than replacing it with a mock.
Only browser-local preferences are changed; no host settings are changed.

Files:

- `overview-light.png`, `overview-dark.png`: CPU, RAM, per-core activity,
  networking, storage, system information, temperatures and process controls.
- `devices-light.png`, `devices-dark.png`: NVMe, accelerators, USB, PCI and cameras.
- `gpu-npu-light.png`, `gpu-npu-dark.png`: live nvtop, Qualcomm access notice and
  accelerator metrics.
