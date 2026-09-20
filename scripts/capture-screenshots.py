#!/usr/bin/env python3
"""Capture the working-tree UI with real telemetry from a running dashboard.

Requires Playwright + Chromium. Usage: python scripts/capture-screenshots.py
Optional first argument: dashboard origin (default http://127.0.0.1:12121).
"""
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'Flask/static'
OUTPUT = ROOT / 'docs/screenshots'
ORIGIN = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:12121'


def local_ui(route):
    """Use current static files, leaving all live API/terminal requests intact."""
    path = unquote(urlparse(route.request.url).path)
    path = {'/': '/index.html', '/accelerators': '/accelerators.html',
            '/systemdevices': '/systemdevices.html'}.get(path, path)
    candidate = (STATIC / path.lstrip('/')).resolve()
    if candidate.is_relative_to(STATIC) and candidate.is_file():
        route.fulfill(path=str(candidate))
    else:
        route.continue_()


def theme(page, mode):
    for _ in range(3):
        if page.locator('html').get_attribute('data-theme') == mode:
            return
        page.locator('#theme-toggle').click()
    raise RuntimeError('Theme control did not switch to ' + mode)


with sync_playwright() as p:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    browser = p.chromium.launch()
    context = browser.new_context(viewport={'width': 1440, 'height': 1100},
                                  device_scale_factor=1, color_scheme='light')
    context.add_init_script("localStorage.setItem('cpu-monitor-theme', 'light');")
    context.route(ORIGIN + '/**', local_ui)
    pages = {}
    errors = []
    for name, path in [('overview', '/'), ('devices', '/systemdevices'), ('gpu-npu', '/accelerators')]:
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(ORIGIN + path, wait_until='domcontentloaded')
        pages[name] = page
    overview = pages['overview']
    overview.locator('#refresh-rate').select_option('1000')
    overview.wait_for_function("document.querySelector('#CPUgraph').data?.[0]?.x?.length >= 20", timeout=60000)
    pages['devices'].wait_for_function("document.querySelector('#refresh-status').textContent.startsWith('Updated')", timeout=30000)
    pages['gpu-npu'].wait_for_function("document.querySelector('#nvtop-status').textContent === 'Live · read-only'", timeout=30000)
    for name, page in pages.items():
        for mode in ['light', 'dark']:
            page.bring_to_front()
            theme(page, mode)
            page.evaluate('document.fonts.ready')
            # Let graph and terminal canvas redraw after the theme change.
            page.wait_for_timeout(1200)
            page.evaluate('window.scrollTo(0, 0)')
            page.screenshot(path=str(OUTPUT / f'{name}-{mode}.png'), full_page=True,
                            animations='disabled')
            print(f'Captured {name}-{mode}.png', flush=True)
    if errors:
        raise RuntimeError('Browser errors: ' + '; '.join(errors))
    browser.close()
