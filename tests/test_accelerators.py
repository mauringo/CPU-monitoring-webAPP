import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Flask'))
from accelerators import collect, number, TelemetryCache


class AcceleratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def device(self, subsystem, node, driver, address='0000:01:00.0'):
        device = self.root / 'bus/pci/devices' / address
        device.mkdir(parents=True, exist_ok=True)
        driver_path = self.root / 'bus/pci/drivers' / driver
        driver_path.mkdir(parents=True, exist_ok=True)
        (device / 'driver').symlink_to(driver_path)
        path = self.root / 'class' / subsystem / node
        path.mkdir(parents=True)
        (path / 'device').symlink_to(device)
        return device

    @patch('accelerators.subprocess.run', side_effect=FileNotFoundError)
    def test_missing_hardware_and_tool(self, run):
        report = collect(self.root)
        self.assertEqual(report['devices'], [])
        self.assertTrue(report['warnings'])

    @patch('accelerators.subprocess.run', side_effect=FileNotFoundError)
    def test_amd_units_and_zero_utilization(self, run):
        device = self.device('drm', 'card0', 'amdgpu')
        for key, value in {'gpu_busy_percent': '0', 'mem_info_vram_used': '1073741824', 'mem_info_vram_total': '4294967296'}.items():
            (device / key).write_text(value)
        hwmon = device / 'hwmon/hwmon0'
        hwmon.mkdir(parents=True)
        (hwmon / 'temp1_input').write_text('42000')
        (hwmon / 'power1_average').write_text('12000000')
        item = collect(self.root)['devices'][0]
        self.assertEqual(item['utilization'], 0)
        self.assertEqual(item['memoryUsed'], 1024**3)
        self.assertEqual(item['temperature'], 42)
        self.assertEqual(item['power'], 12)

    @patch('accelerators.subprocess.run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 2))
    def test_npu_dedup_and_missing_utilization(self, run):
        self.device('accel', 'accel0', 'amdxdna')
        result = collect(self.root)
        self.assertEqual(len(result['devices']), 1)
        self.assertEqual(result['devices'][0]['kind'], 'NPU')
        self.assertIsNone(result['devices'][0]['utilization'])
        self.assertTrue(result['warnings'])

    @patch('accelerators.subprocess.run')
    def test_nvidia_merge_and_unsupported_metrics(self, run):
        self.device('drm', 'card0', 'nvidia')
        run.return_value = subprocess.CompletedProcess([], 0, 'GPU-uuid, 00000000:01:00.0, "NVIDIA, Example", 75, 1024, 8192, [N/A], NaN\n')
        devices = collect(self.root)['devices']
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['name'], 'NVIDIA, Example')
        self.assertEqual(devices[0]['memoryUsed'], 1024**3)
        self.assertEqual(devices[0]['utilization'], 75)
        self.assertIsNone(devices[0]['temperature'])
        self.assertIsNone(devices[0]['power'])
        self.assertEqual(run.call_args.kwargs['timeout'], 2)

    @patch('accelerators.subprocess.run')
    def test_malformed_vendor_output(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'unexpected output\n')
        report = collect(self.root)
        self.assertEqual(report['devices'], [])
        self.assertTrue(report['warnings'])

    @patch('accelerators.subprocess.run', side_effect=FileNotFoundError)
    def test_render_only_gpu_is_discovered(self, run):
        self.device('drm', 'renderD128', 'panfrost')
        report = collect(self.root)
        self.assertEqual(len(report['devices']), 1)
        self.assertEqual(report['devices'][0]['driver'], 'panfrost')

    def test_invalid_numbers_are_unknown(self):
        for value in ['NaN', 'Infinity', '-1', '', '[Not Supported]', None]:
            self.assertIsNone(number(value))

    @patch('accelerators.collect', return_value={'devices': []})
    @patch('accelerators.time.monotonic', side_effect=[10, 11, 13, 13])
    def test_cache_shares_samples_and_expires(self, clock, collect_mock):
        cache = TelemetryCache()
        cache.get()
        cache.get()
        self.assertEqual(collect_mock.call_count, 1)
        cache.get()
        self.assertEqual(collect_mock.call_count, 2)
