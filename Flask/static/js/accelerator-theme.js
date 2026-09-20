// Apply the saved dashboard theme before the page paints.
(() => {
    const key = 'cpu-monitor-theme';
    const modes = ['system', 'light', 'dark'];
    const system = matchMedia('(prefers-color-scheme: dark)');
    let mode = 'system';
    try { mode = localStorage.getItem(key) || mode; } catch (_) { /* Storage may be disabled. */ }
    if (!modes.includes(mode)) mode = 'system';
    function apply() {
        document.documentElement.dataset.theme = mode;
        document.documentElement.style.colorScheme = mode === 'system' ? (system.matches ? 'dark' : 'light') : mode;
        const button = document.getElementById('theme-toggle');
        if (button) button.textContent = 'Theme: ' + mode;
        window.dispatchEvent(new Event('monitor-theme-change'));
    }
    apply();
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('theme-toggle').addEventListener('click', () => {
            mode = modes[(modes.indexOf(mode) + 1) % modes.length];
            try { localStorage.setItem(key, mode); } catch (_) { /* Keep the in-page preference. */ }
            apply();
        });
        apply();
    });
    system.addEventListener('change', () => { if (mode === 'system') apply(); });
    window.addEventListener('storage', event => {
        if (event.key === key || event.key === null) {
            mode = modes.includes(event.newValue) ? event.newValue : 'system';
            apply();
        }
    });
})();
