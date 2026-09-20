[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

# CPU Monitoring

CPU Monitoring is a lightweight Linux system dashboard served by Flask. Open
`http://yourDeviceIp:12121` in a browser to view live CPU and RAM usage,
per-core activity, network traffic, disk usage, temperature sensors, process
activity, and system information.

The dashboard includes interactive CPU and RAM history graphs with CSV export.
Its Devices page lists USB and PCI hardware, cameras, NVMe storage,
accelerators, and additional host information. Temperature readings, hardware
discovery, and process monitoring depend on the Snap permissions described
below.

The dashboard is available at `http://localhost:12121` when the server is
running. The application uses Waitress and does not require an external web
server.

## Features

- Live CPU and RAM usage with history charts
- Physical and logical CPU counts, architecture, kernel, and processor details
- Temperature sensor readings when the platform exposes them
- Top processes by CPU and memory usage
- Network traffic and physical disk inventory from `lsblk` (loop devices excluded)
- Network interface names and addresses from `ifconfig`
- NVMe controller and namespace discovery
- Linux accelerator and NPU discovery
- Device inspection tools exposed through the Devices page
- Light, dark, and system theme modes
- A Help menu with live Snap permission and utility checks

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

The source server listens on `0.0.0.0:12121`, so it can be reached from
another device on the same network. Change the port in `Flask/app.py` if a
different port is required.

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

The project targets `amd64`, `arm64`, `armhf`, `ppc64el`, `riscv64`, and
`s390x`; `i386` is intentionally excluded. Snapcraft may use a managed Ubuntu
build instance when the host OS does not match the `core26` build environment.

For a locally built Snap file, use `--dangerous` because the file is not signed
by the Snap Store:

```sh
sudo snap remove cpu-monitoring-webapp 2>/dev/null || true
sudo snap install ./cpu-monitoring-webapp_*.snap --dangerous
```

For the published Store package, use the simpler command:

```sh
sudo snap install cpu-monitoring-webapp --devmode
```

After changing `snapcraft.yaml` or application files, rebuild and reinstall the
Snap. An already-installed revision does not contain newly added plugs or
static files.

## Snap permissions

Strict confinement limits access to hardware and other processes. Connect the
interfaces below after installing the Snap. The first group enables the
dashboard and hardware inventory; `process-control` grants the OS permission
for the Stop action. A configured `MONITOR_CONTROL_TOKEN` is also required:

```sh
sudo snap connect cpu-monitoring-webapp:network
sudo snap connect cpu-monitoring-webapp:network-control
sudo snap connect cpu-monitoring-webapp:network-bind
sudo snap connect cpu-monitoring-webapp:network-observe
sudo snap connect cpu-monitoring-webapp:gsettings
sudo snap connect cpu-monitoring-webapp:hardware-observe
sudo snap connect cpu-monitoring-webapp:system-observe
sudo snap connect cpu-monitoring-webapp:process-control
sudo snap connect cpu-monitoring-webapp:raw-usb
sudo snap connect cpu-monitoring-webapp:camera
sudo snap connect cpu-monitoring-webapp:mount-observe
sudo snap connect cpu-monitoring-webapp:udisks2
```

Some interfaces may already be auto-connected or may not be available on every
system. A failed `snap connect` for an unavailable interface can be skipped.
The Flask service checks these interfaces and monitoring commands at boot. The
Overview page's **Help** menu exposes the current connection state, available
utilities, and the commands needed to connect missing interfaces or run a local
devmode test. The same report is available at `/permissions`.
The menu also provides one command that connects all declared interfaces. Copy
and paste it into a terminal only if you understand the requested access.
Disclaimer: use at your own risk.
The application still reports CPU, memory, network totals, disk usage, and
processes when the corresponding platform data is accessible. Missing kernel
drivers, utilities, or Snap permissions can prevent hardware from appearing;
an empty device list does not prove that the hardware is absent.

### Permission purposes

- `network` and `network-bind`: allow the service to serve the dashboard.
- `network-observe`: allow network device and traffic observation.
- `hardware-observe` and `system-observe`: allow hardware, system, and process
	observation.
- `process-control`: grants OS access for Stop; `MONITOR_CONTROL_TOKEN` also must be configured.
- `raw-usb`: allows USB device discovery.
- `camera`: allows access to camera devices used by `v4l2-ctl`.
- `mount-observe` and `udisks2`: allow mounted-storage and disk information.
- `gsettings`: supports the desktop launcher environment.

The `camera` interface is only present in Snap revisions built after camera
support was added. If `snap connections cpu-monitoring-webapp` does not list
it, rebuild and reinstall the Snap before running:

```sh
sudo snap connect cpu-monitoring-webapp:camera
```

## Disk and camera troubleshooting

Disk inventory uses `lsblk --json --bytes --tree`. Physical disks are shown,
loop devices are excluded, and filesystem usage is calculated from mounted
partitions with `psutil.disk_usage()`. A disk can therefore show its size while
reporting no usage when it has no mounted filesystem.

Network interface discovery uses `ifconfig -a`, provided by the Snap's
`net-tools` staged package. The existing `network-observe` interface remains
the relevant permission for network inspection.

Camera discovery uses:

```sh
v4l2-ctl --list-devices
```

An empty camera list means there is no accessible V4L2 camera, the `camera`
interface is not connected, or the camera driver is unavailable. Check the
service log and the interface state:

```sh
snap connections cpu-monitoring-webapp
sudo snap logs cpu-monitoring-webapp.flask-server
```

USB discovery first uses `lsusb` and falls back to read-only USB sysfs data when
the command is unavailable. Connect `raw-usb` for the most complete USB view:

```sh
sudo snap connect cpu-monitoring-webapp:raw-usb
```

## Process monitoring note

The current process tables are requested by the browser and sampled while the
task monitor is enabled. Because the Flask/Waitress Python service handles
those requests, Python can temporarily appear near the top of CPU usage. That
is a measurement effect, not necessarily a workload from another application.

A better future design is a background sampler that collects process data on a
fixed interval, caches one snapshot, and lets `/processes` return the cached
result without scanning processes during every browser request. The sampler
should identify the monitoring service by PID and creation time, report it in a
separate “monitor overhead” row, and optionally exclude it from the top-user
tables. This keeps the dashboard responsive and makes the process ranking less
correlated with frontend polling.

To inspect service failures:

```sh
sudo snap logs cpu-monitoring-webapp.flask-server
```

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

This project is licensed under the GNU General Public License, version 3 only
(`GPL-3.0-only`). See [LICENSE](LICENSE). Original attribution is retained in
[NOTICE](NOTICE). Bundled third-party components retain their respective
licenses and copyright notices.

## GPU / NPU visualization

Open `/accelerators` or choose **GPU / NPU** in the navigation. The page polls
`/acceleratordata` every three seconds and retains 60 samples per device. It
includes utilization graphs, video memory, temperature, power, pause/resume,
and disconnected/empty states. Multiple clients share a two-second server cache;
NVIDIA queries have a two-second timeout.

- NVIDIA: metrics from `nvidia-smi`, when installed and accessible to the service.
- AMD (`amdgpu`): utilization and VRAM from documented Linux sysfs counters.
- Other DRM GPUs: discovery and available hwmon temperature/power sensors.
- NPUs: discovery through Linux `accel` and known PCI/platform drivers, including
  Intel, AMD XDNA, Rockchip, Ethos and Hailo. Available hwmon sensors are displayed.
  NPU utilization is currently unavailable; vendor-specific collectors are needed.
  Generic `accel` devices are labeled **Accelerator**, since not all are NPUs.

Missing readings are `null` in the API and shown as a dash, never as zero load.
Containers and strict Snaps may restrict sysfs/device access or vendor tools;
this page does not install drivers, elevate permissions or bypass confinement.
The underlying sysfs metrics are documented in the
[Linux AMD GPU monitoring documentation](https://docs.kernel.org/gpu/amdgpu/thermal.html).

### Embedded nvtop terminal

The GPU / NPU page automatically opens a live, read-only **nvtop** terminal.
It uses a Linux pseudo-terminal and Server-Sent Events at `/nvtop/stream`,
rendered by a locally bundled xterm.js 5.5.0. Colors, graphs and cursor updates
come directly from nvtop. No ttyd, external CDN, WebSocket server or extra port
is needed. Use **Disconnect terminal** / **Reconnect terminal** to control the
view; the chart pause button controls only dashboard charts.

Install `nvtop` on the monitored host and ensure it is on the service's PATH.
Snap builds now include the nvtop package (rebuild/reinstall the Snap to include
it). The native service account must be able to access the GPU/accelerator
and allocate a PTY. Strict Snap confinement may additionally restrict PTYs or
hardware; the page reports launch failures instead of elevating privileges.
NPU visibility depends on the installed nvtop version and driver support.

The bundled `Flask/nvtop.ini` disables blocking startup information dialogs
without changing your personal nvtop configuration.

Terminal input is disabled: the server accepts neither keystrokes nor commands.
There are at most two terminal sessions per server process, with a ten-minute
limit per session. Closing a stream terminates and reaps its nvtop subprocess.
Waitress runs eight worker threads to leave capacity for normal dashboard
requests. Custom WSGI deployments should provide more workers than the two
stream slots. Reverse proxies must disable response buffering for `/nvtop/stream`
and allow long-lived responses. Terminal geometry is selected when connecting;
on narrow screens the terminal scrolls horizontally.

Like the existing read-only dashboard, this endpoint has no authentication.
Use a trusted network or an authenticated reverse proxy for remote access.
The xterm.js MIT license is retained in `Flask/static/libs/xterm/LICENSE`.

### Process control

Process termination is now **disabled by default**. To enable it, set a strong
`MONITOR_CONTROL_TOKEN` in the server environment and restart the service.
The Stop action asks for that token and sends it in the Authorization header;
it is not stored in browser storage. Use HTTPS or an SSH tunnel when using
process control remotely. The token grants the service's process-termination
privileges; the read-only dashboard endpoints still have no authentication.
Process RAM values now report resident memory (RSS) in MiB. The `/processes`
API uses `rss` in place of the previous misleading `vms` field.

Run regression tests with `python3 -m unittest discover -s tests -v` after
installing `requirements.txt`.

Optional browser checks: install `playwright`, run `python3 -m playwright install chromium`,
then `python3 tests/browser_accelerators.py` (Chromium system libraries are required).
