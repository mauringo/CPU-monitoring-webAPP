import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Flask'))


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cwd = os.getcwd()
        # Import without the legacy startup sampler or permission subprocesses.
        with patch('threading.Thread.start'), patch('subprocess.run', side_effect=FileNotFoundError), patch('builtins.print'):
            cls.module = importlib.import_module('app')
        os.chdir(cwd)
        cls.client = cls.module.app.test_client()

    def test_page_and_json(self):
        with self.client.get('/accelerators') as page:
            self.assertEqual(page.status_code, 200)
        with patch.object(self.module.ACCELERATOR_CACHE, 'get', return_value={'devices': [], 'warnings': [], 'sampledAt': 1}):
            response = self.client.get('/acceleratordata')
        self.assertEqual(response.json['devices'], [])
        self.assertEqual(response.mimetype, 'application/json')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_terminal_route_bounds_dimensions_and_blocks_cross_site(self):
        with patch.object(self.module, 'stream_nvtop', return_value=iter([': test\n\n'])) as stream:
            with self.client.get('/nvtop/stream?columns=9999') as response:
                self.assertEqual(response.mimetype, 'text/event-stream')
                self.assertEqual(response.headers['X-Accel-Buffering'], 'no')
                stream.assert_called_once_with(columns=160)
        self.assertEqual(self.client.get('/nvtop/stream', headers={'Sec-Fetch-Site': 'cross-site'}).status_code, 403)

    def test_termination_disabled_without_configuration(self):
        with patch.dict(os.environ, {'MONITOR_CONTROL_TOKEN': ''}), patch.object(self.module.psutil, 'Process') as process:
            self.assertEqual(self.client.post('/processes/12345/terminate').status_code, 403)
            process.assert_not_called()

    def test_termination_requires_token(self):
        with patch.dict(os.environ, {'MONITOR_CONTROL_TOKEN': 'test-secret'}), patch.object(self.module.psutil, 'Process') as process:
            for headers in [{}, {'Authorization': 'Bearer wrong'}, {'Authorization': 'Bearer café'}]:
                self.assertEqual(self.client.post('/processes/12345/terminate', headers=headers).status_code, 403)
            process.assert_not_called()
            response = self.client.post('/processes/12345/terminate', headers={'Authorization': 'Bearer test-secret'})
            self.assertEqual(response.status_code, 200)
            process.return_value.terminate.assert_called_once()
            self.assertEqual(self.client.post('/processes/1/terminate', headers={'Authorization': 'Bearer test-secret'}).status_code, 400)

    def test_memory_sampler_uses_resident_memory(self):
        process = MagicMock()
        process.as_dict.return_value = {'pid': 42, 'name': 'test', 'username': 'test', 'cpu_percent': 1}
        process.memory_info.return_value.rss = 10 * 1024**2
        process.memory_info.return_value.vms = 1000 * 1024**2
        with patch.object(self.module.psutil, 'process_iter', return_value=[process]):
            self.module.refreshProcessCache()
        self.assertEqual(self.module.PROCESS_CACHE['ramProcesses'][0]['rss'], 10)
