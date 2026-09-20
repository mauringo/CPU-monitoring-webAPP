"""Bounded, read-only accelerator telemetry. Missing metrics are None, never zero."""
import csv
import math
from pathlib import Path
import re
import subprocess
import threading
import time

from devices import entries, read_text

NPU_DRIVERS = {'intel_vpu', 'ivpu', 'amdxdna', 'rknpu', 'ethosu', 'ethos-u', 'hailo_pci'}
VENDORS = {'0x1002': 'AMD', '0x8086': 'Intel', '0x10de': 'NVIDIA'}


def number(value, scale=1):
    try:
        result = float(value) / scale
        return result if math.isfinite(result) and result >= 0 else None
    except (TypeError, ValueError):
        return None


def record(identity, name, kind, driver, source):
    return dict(id=identity, name=name, kind=kind, driver=driver, source=source,
                utilization=None, memoryUsed=None, memoryTotal=None,
                temperature=None, power=None)


def pci_key(address):
    # NVIDIA prints an eight-digit PCI domain; Linux normally uses four.
    match = re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7])', address)
    return f'{int(match[1], 16):04x}:{match[2].lower()}' if match else address


def collect(sysfs=Path('/sys')):
    devices, warnings = {}, []
    for subsystem, pattern in [('drm', r'(?:card|renderD)\d+'), ('accel', r'accel\d+')]:
        for node in entries(sysfs / 'class' / subsystem):
            if re.fullmatch(pattern, node.name) and (node / 'device').exists():
                device = (node / 'device').resolve()
                devices[str(device)] = (device, node.name, subsystem == 'accel')
    for bus in ['pci', 'platform']:
        for device in entries(sysfs / 'bus' / bus / 'devices'):
            driver = (device / 'driver').resolve().name
            if driver in NPU_DRIVERS:
                devices.setdefault(str(device.resolve()), (device.resolve(), device.name, True))

    result = []
    for device, label, accelerator in devices.values():
        driver = (device / 'driver').resolve().name if (device / 'driver').exists() else ''
        kind = 'NPU' if driver in NPU_DRIVERS else ('Accelerator' if accelerator else 'GPU')
        vendor = VENDORS.get(read_text(device / 'vendor'), '')
        item = record(str(device), ' '.join(filter(None, [vendor, driver or label, read_text(device / 'device')])), kind, driver, 'Linux sysfs')
        item['pciAddress'] = pci_key(device.name)
        # gpu_busy_percent and VRAM counters are documented amdgpu interfaces.
        if driver == 'amdgpu':
            busy = number(read_text(device / 'gpu_busy_percent'))
            item['utilization'] = busy if busy is not None and busy <= 100 else None
            item['memoryUsed'] = number(read_text(device / 'mem_info_vram_used'))
            item['memoryTotal'] = number(read_text(device / 'mem_info_vram_total'))
        for hwmon in entries(device / 'hwmon'):
            if item['temperature'] is None:
                item['temperature'] = number(read_text(hwmon / 'temp1_input'), 1000)
            if item['power'] is None:
                item['power'] = number(read_text(hwmon / 'power1_average'), 1000000)
        result.append(item)
    try:
        query = 'uuid,pci.bus_id,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw'
        output = subprocess.run(['nvidia-smi', '--query-gpu=' + query, '--format=csv,noheader,nounits'],
                                capture_output=True, text=True, timeout=2, check=True)
        for row in csv.reader(output.stdout.splitlines(), skipinitialspace=True):
            if len(row) != 8:
                warnings.append('An NVIDIA telemetry row could not be read.')
                continue
            uuid, address, name, busy, used, total, temperature, power = [v.strip() for v in row]
            address = pci_key(address)
            item = next((d for d in result if d.get('pciAddress') == address), None)
            if item is None:
                item = record(uuid, name, 'GPU', 'nvidia', 'nvidia-smi')
                result.append(item)
            item.update(name=name, source='nvidia-smi', pciAddress=address,
                        utilization=number(busy), memoryUsed=number(used, 1 / 1024**2),
                        memoryTotal=number(total, 1 / 1024**2), temperature=number(temperature), power=number(power))
            if item['utilization'] is not None and item['utilization'] > 100:
                item['utilization'] = None
    except FileNotFoundError:
        warnings.append('nvidia-smi is not installed or accessible; NVIDIA metrics may be unavailable.')
    except (OSError, subprocess.SubprocessError):
        warnings.append('NVIDIA telemetry failed or timed out; check the driver and device permissions.')
    return {'devices': result, 'warnings': warnings, 'sampledAt': time.time()}


class TelemetryCache:
    """Serialize refreshes so multiple browser tabs share one sample."""
    def __init__(self):
        self.lock = threading.Lock()
        self.value = None
        self.updated = 0

    def get(self):
        with self.lock:
            if self.value is None or time.monotonic() - self.updated >= 2:
                self.value = collect()
                self.updated = time.monotonic()
            return self.value
