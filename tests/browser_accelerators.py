"""Optional browser regression check: requires playwright and installed Chromium."""
import importlib
import os
from pathlib import Path
import sys
import threading
from unittest.mock import patch

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Flask'))
cwd = os.getcwd()
with patch('threading.Thread.start'), patch('subprocess.run', side_effect=FileNotFoundError), patch('builtins.print'):
    app = importlib.import_module('app').app
os.chdir(cwd)
server = make_server('127.0.0.1', 0, app, threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}'
report = {'devices': [
    dict(id='gpu', kind='GPU', name='<img src=x onerror=alert(1)> Example GPU', source='Fixture', driver='amdgpu', utilization=42, memoryUsed=1024**3, memoryTotal=8*1024**3, temperature=51, power=63),
    dict(id='npu', kind='NPU', name='Example NPU', source='Fixture', driver='amdxdna', utilization=None, memoryUsed=None, memoryTotal=None, temperature=None, power=None),
], 'warnings': [], 'sampledAt': 1700000000}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/nvtop/stream?*', lambda route: route.fulfill(content_type='text/event-stream', body='event: output\ndata: "R1BVIGxpdmU="\n\nevent: finished\ndata: {"message": "Terminal fixture finished"}\n\n'))
        page.route('**/acceleratordata', lambda route: route.fulfill(json=report))
        page.goto(base + '/accelerators')
        page.wait_for_selector('.js-plotly-plot')
        page.wait_for_function("document.querySelector('#nvtop-status').textContent === 'Terminal fixture finished'")
        assert page.locator('#nvtop-terminal .xterm').count() == 1
        page.get_by_role('button', name='Reconnect terminal').click()
        page.wait_for_function("document.querySelector('#nvtop-status').textContent === 'Terminal fixture finished'")
        assert page.locator('.accelerator-card').count() == 2
        assert page.locator('.accelerator-card img').count() == 0
        assert '42.0%' in page.locator('.accelerator-card').first.inner_text()
        assert 'Utilization unavailable' in page.locator('.accelerator-card').nth(1).inner_text()
        page.get_by_role('button', name='Pause updates').click()
        assert page.locator('#pause').get_attribute('aria-pressed') == 'true'
        page.get_by_role('button', name='Resume updates').click()
        page.screenshot(path='/tmp/cpu-monitor-accelerators-desktop.png', full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.wait_for_function("document.querySelector('.js-plotly-plot .main-svg').getBoundingClientRect().width <= document.querySelector('.accelerator-chart').clientWidth")
        page.screenshot(path='/tmp/cpu-monitor-accelerators-mobile.png', full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        report['devices'] = []
        page.reload()
        page.wait_for_function("document.querySelector('#accelerator-list').textContent.includes('No accessible GPUs')")
        page.unroute('**/acceleratordata')
        page.route('**/acceleratordata', lambda route: route.fulfill(status=503, body='Unavailable'))
        page.reload()
        page.wait_for_function("document.querySelector('#status').textContent.includes('Disconnected')")
        # Check the overview renders hostile hardware labels as text.
        page.goto(base + '/')
        page.evaluate("""() => renderResourceUsage({sent: 0, received: 0, interfaces: [{name: '<img src=x>', addresses: ['<img src=x>']}]}, {disks: [{name: '<img src=x>', model: '<img src=x>', size: 1, filesystems: [{mountpoint: '<img src=x>', usedPercent: '20%'}]}]})""")
        assert page.locator('#disk-list img, #network-interfaces img').count() == 0
        assert not errors, errors
        browser.close()
        print('Browser checks passed: metrics, unknown readings, HTML safety, pause/resume, mobile, empty/error states.')
finally:
    server.shutdown()
    thread.join(timeout=5)
