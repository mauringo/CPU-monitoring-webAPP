import base64
import sys
from pathlib import Path
import threading
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Flask'))
import nvtop_stream as nvtop


class NvtopTests(unittest.TestCase):
    def setUp(self):
        self.slots = threading.BoundedSemaphore(1)
        patcher = patch.object(nvtop, 'SLOTS', self.slots)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_released(self):
        self.assertTrue(self.slots.acquire(blocking=False))
        self.slots.release()

    @patch('nvtop_stream.shutil.which', return_value=None)
    def test_missing_binary(self, which):
        self.assertIn('not installed', ''.join(nvtop.stream_nvtop()))
        self.assert_released()

    def test_capacity_limit(self):
        self.slots.acquire()
        self.assertIn('already connected', ''.join(nvtop.stream_nvtop()))
        self.slots.release()

    @patch('nvtop_stream.shutil.which', return_value='/usr/bin/nvtop')
    @patch('nvtop_stream.pty.openpty', side_effect=PermissionError)
    def test_pty_failure_releases_slot(self, openpty, which):
        self.assertIn('Unable to run', ''.join(nvtop.stream_nvtop()))
        self.assert_released()

    @patch('nvtop_stream.shutil.which', return_value='/usr/bin/nvtop')
    @patch('nvtop_stream.pty.openpty', return_value=(10, 11))
    @patch('nvtop_stream.fcntl.ioctl')
    @patch('nvtop_stream.os.close')
    @patch('nvtop_stream.os.read', return_value=b'\x1b[32mGPU 50%\x1b[0m')
    @patch('nvtop_stream.select.select', return_value=([10], [], []))
    @patch('nvtop_stream.subprocess.Popen')
    def test_stream_preserves_ansi_and_disconnect_cleans_up(self, popen, select, read, close, ioctl, pty, which):
        process = popen.return_value
        process.poll.return_value = None
        stream = nvtop.stream_nvtop(100)
        self.assertIn('ready', next(stream))
        output = next(stream)
        self.assertIn(base64.b64encode(read.return_value).decode(), output)
        stream.close()
        process.terminate.assert_called_once()
        process.wait.assert_called_once()
        self.assertEqual({call.args[0] for call in close.call_args_list}, {10, 11})
        self.assertEqual(popen.call_args.args[0][:4], ['/usr/bin/nvtop', '-d', '10', '-c'])
        self.assertEqual(Path(popen.call_args.args[0][4]).name, 'nvtop.ini')
        self.assertNotIn('shell', popen.call_args.kwargs)
        self.assert_released()
