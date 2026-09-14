import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Flask'))
from devices import discover_nvme, discover_npus


class DeviceDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path.parent

    def test_nvme_capacity_excludes_partitions(self):
        self.write('class/nvme/nvme0/model', 'Example SSD')
        self.write('class/nvme/nvme0/state', 'live')
        self.write('class/block/nvme0n1/size', '2097152')
        self.write('class/block/nvme0n1p1/size', '1024')
        self.assertEqual(discover_nvme(self.root), ['nvme0 — Example SSD — live — /dev/nvme0n1 (1.0 GiB)'])

    @patch('devices.subprocess.run', side_effect=FileNotFoundError)
    def test_missing_sysfs_and_pci_tool(self, run):
        self.assertEqual(discover_nvme(self.root), [])
        self.assertEqual(discover_npus(self.root), [])

    @patch('devices.subprocess.run')
    def test_accelerator_and_pci_are_deduplicated(self, run):
        device = self.write('bus/pci/devices/0000:00:0b.0/vendor', '0x8086')
        self.write('bus/pci/devices/0000:00:0b.0/device', '0x1234')
        driver = self.root / 'bus/pci/drivers/intel_vpu'
        driver.mkdir(parents=True)
        (device / 'driver').symlink_to(driver)
        accel = self.root / 'class/accel/accel0'
        accel.mkdir(parents=True)
        (accel / 'device').symlink_to(device)
        run.return_value = subprocess.CompletedProcess([], 0, '0000:00:0b.0 Processing accelerators: Intel NPU\n0000:00:02.0 VGA controller: GPU\n')
        result = discover_npus(self.root)
        self.assertEqual(len(result), 1)
        self.assertIn('intel_vpu', result[0])

    @patch('devices.subprocess.run', side_effect=subprocess.TimeoutExpired('lspci', 5))
    def test_platform_npu_survives_pci_timeout(self, run):
        device = self.root / 'bus/platform/devices/fdab0000.npu'
        device.mkdir(parents=True)
        driver = self.root / 'bus/platform/drivers/rknpu'
        driver.mkdir(parents=True)
        (device / 'driver').symlink_to(driver)
        self.assertEqual(discover_npus(self.root), ['fdab0000.npu — rknpu'])


if __name__ == '__main__':
    unittest.main()
