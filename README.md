![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# CPU Monitoring

CPU Monitoring is a lightweight Linux system dashboard served by Flask. It
shows live CPU and memory usage, system information, temperature sensors, top
processes, storage devices, and available accelerator/NPU hardware.

The dashboard is available at `http://localhost:12121` when the server is
running. The application uses Waitress and does not require an external web
server.

## Features

- Live CPU and RAM usage with history charts
- Physical and logical CPU counts, architecture, kernel, and processor details
- Temperature sensor readings when the platform exposes them
- Top processes by CPU and memory usage
- NVMe controller and namespace discovery
- Linux accelerator and NPU discovery
- Device inspection tools exposed through the Devices page

## Install from the Snap Store

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/cpu-monitoring-webapp)

```sh
sudo snap install --edge cpu-monitoring-webapp
```

Open `http://localhost:12121` after installation. The Snap runs the Flask
server as a service and provides a desktop launcher for the dashboard.

## Run from source

Python 3 and `pip` are required.

```sh
git clone https://github.com/mauringo/CPU-monitoring-webAPP.git
cd CPU-monitoring-webAPP
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python Flask/app.py
```

Then open [http://localhost:12121](http://localhost:12121). Stop the server
with `Ctrl+C`.

## Run the tests

The device discovery tests use temporary mock sysfs trees, so they can run
without special hardware:

```sh
python -m unittest discover -s tests -v
```

## Build a Snap

Install Snapcraft and its build provider according to the
[Snapcraft documentation](https://snapcraft.io/docs/installing-snapcraft). In
the repository root, run:

```sh
snapcraft pack
sudo snap install --dangerous ./cpu-monitoring-webapp_*.snap
```

For a local test build using a different package name, install the generated
file shown by `snapcraft pack` instead of relying on a fixed filename.

## Hardware permissions

The strictly confined Snap may need hardware observation interfaces for device
discovery:

```sh
sudo snap connect cpu-monitoring-webapp:hardware-observe
sudo snap connect cpu-monitoring-webapp:system-observe
sudo snap logs cpu-monitoring-webapp.flask-server
```

Missing kernel drivers, utilities, or Snap permissions can prevent hardware
from appearing. An empty device list does not prove that the hardware is
absent.

## Project layout

```text
Flask/app.py              Flask routes and system metrics
Flask/devices.py          Linux NVMe and accelerator discovery
Flask/static/             Dashboard HTML, CSS, JavaScript, and assets
shscripts/                Snap service and desktop launch scripts
snapcraft.yaml            Snap package definition
tests/                    Device discovery tests
```

## Platform support

The current hardware discovery implementation is Linux-specific. Core process,
CPU, and memory metrics use `psutil`, but `/sys`, `lspci`, `lsusb`, and
`v4l2-ctl` discovery are not portable to macOS or Windows without a platform
adapter.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
