"""Read-only nvtop PTY sessions transported as server-sent events."""
import base64
import errno
import fcntl
import json
import os
import pty
from pathlib import Path
import select
import shutil
import struct
import subprocess
import termios
import threading
import time

# Each stream occupies one WSGI worker. Leave capacity for dashboard requests.
SLOTS = threading.BoundedSemaphore(2)
MAX_SECONDS = 600


def event(kind, data):
    return f'event: {kind}\ndata: {json.dumps(data)}\n\n'


def stream_nvtop(columns=120, rows=36):
    """Never accepts a command or terminal input from the browser."""
    if not SLOTS.acquire(blocking=False):
        yield event('finished', {'message': 'Two terminal viewers are already connected. Disconnect one and retry.'})
        return
    master = slave = None
    process = None
    try:
        executable = shutil.which('nvtop')
        if not executable:
            yield event('finished', {'message': 'nvtop is not installed or accessible to the dashboard service.'})
            return
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))
        environment = dict(os.environ, TERM='xterm-256color')
        process = subprocess.Popen([executable, '-d', '10', '-c', str(Path(__file__).with_name('nvtop.ini'))], stdin=slave, stdout=slave,
                                   stderr=slave, env=environment, start_new_session=True,
                                   close_fds=True)
        os.close(slave)
        slave = None
        yield event('ready', {'columns': columns, 'rows': rows})
        deadline = time.monotonic() + MAX_SECONDS
        while time.monotonic() < deadline:
            readable, _, _ = select.select([master], [], [], 1)
            if readable:
                try:
                    output = os.read(master, 16384)
                except OSError as error:
                    if error.errno == errno.EIO:  # Linux PTY EOF
                        break
                    raise
                if not output:
                    break
                yield event('output', base64.b64encode(output).decode('ascii'))
            else:
                # Flush regularly so a disconnected viewer releases its PTY.
                yield ': heartbeat\n\n'
                if process.poll() is not None:
                    break
        if process.poll() is None:
            message = 'Session reached its 10-minute limit. Reconnect to continue.'
        else:
            message = f'nvtop exited (code {process.returncode}). Check terminal output and hardware access.'
        yield event('finished', {'message': message})
    except (OSError, subprocess.SubprocessError):
        yield event('finished', {'message': 'Unable to run nvtop. Check executable and PTY/device permissions.'})
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            else:
                process.wait()
        for descriptor in [master, slave]:
            if descriptor is not None:
                os.close(descriptor)
        SLOTS.release()
