"""Read-only Linux hardware discovery; no vendor SDK or device access required."""
from pathlib import Path
import re
import subprocess


def read_text(path):
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return ''


def entries(path):
    try:
        return sorted(path.iterdir())
    except OSError:
        return []


def discover_nvme(sysfs=Path('/sys')):
    devices = []
    for controller in entries(sysfs / 'class/nvme'):
        details = [controller.name, read_text(controller / 'model'),
                   read_text(controller / 'state')]
        namespaces = []
        for block in entries(sysfs / 'class/block'):
            if re.fullmatch(re.escape(controller.name) + r'n\d+', block.name):
                size = read_text(block / 'size')
                capacity = f' ({int(size) * 512 / 1024**3:.1f} GiB)' if size.isdigit() else ''
                namespaces.append('/dev/' + block.name + capacity)
        details.extend(namespaces)
        devices.append(' — '.join(filter(None, details)))
    return devices


def discover_npus(sysfs=Path('/sys')):
    devices = {}
    # The accel subsystem includes NPUs and other compute accelerators.
    for accelerator in entries(sysfs / 'class/accel'):
        if not re.fullmatch(r'accel\d+', accelerator.name):
            continue
        device = (accelerator / 'device').resolve()
        driver = (device / 'driver').resolve().name if (device / 'driver').exists() else ''
        details = [accelerator.name, driver, read_text(device / 'vendor'), read_text(device / 'device')]
        devices[str(device)] = ' — '.join(filter(None, details))
    # Embedded NPUs can use platform drivers instead of the accel subsystem.
    for bus in ['pci', 'platform']:
        for device in entries(sysfs / 'bus' / bus / 'devices'):
            driver = (device / 'driver').resolve().name if (device / 'driver').exists() else ''
            if driver in {'intel_vpu', 'amdxdna', 'ivpu', 'rknpu', 'ethosu', 'ethos-u', 'hailo_pci'}:
                devices.setdefault(str(device.resolve()), f'{device.name} — {driver}')
    # Include explicitly named PCI NPUs even when no driver is loaded.
    try:
        result = subprocess.run(['lspci', '-D'], capture_output=True, text=True, timeout=5, check=True)
        for line in result.stdout.splitlines():
            if re.search(r'\bNPU\b|neural|neuro|\bVPU\b|Movidius|Hailo', line, re.I):
                address = line.split()[0]
                devices.setdefault(str((sysfs / 'bus/pci/devices' / address).resolve()), line)
    except (OSError, subprocess.SubprocessError):
        pass
    return list(devices.values())
