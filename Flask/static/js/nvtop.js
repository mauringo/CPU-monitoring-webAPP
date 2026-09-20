'use strict';
(() => {
    const host = document.getElementById('nvtop-terminal');
    const status = document.getElementById('nvtop-status');
    const toggle = document.getElementById('nvtop-toggle');
    const columns = Math.max(80, Math.min(160, Math.floor((host.parentElement.clientWidth - 24) / 7.8)));
    const terminal = new Terminal({cols: columns, rows: 36, fontSize: 13,
        fontFamily: 'monospace', disableStdin: true, cursorBlink: false,
        scrollback: 0, minimumContrastRatio: 4.5});
    function applyTerminalTheme() {
        const css = getComputedStyle(document.documentElement);
        const mode = document.documentElement.dataset.theme;
        const dark = mode === 'dark' || (mode === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
        const palette = dark
            ? ['#162639', '#ff8585', '#83d990', '#e9cc75', '#8cb8ff', '#dba1ef', '#73d4dc', '#e7eef7']
            : ['#152b46', '#b42335', '#247339', '#856400', '#245ec4', '#8740a3', '#007780', '#f3f6fa'];
        terminal.options.theme = {
            background: css.getPropertyValue('--surface').trim(),
            foreground: css.getPropertyValue('--ink').trim(),
            cursor: css.getPropertyValue('--ink').trim(),
            selectionBackground: dark ? '#365779' : '#c4d8fa',
            ...Object.fromEntries(['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'].flatMap((name, i) =>
                [[name, palette[i]], ['bright' + name[0].toUpperCase() + name.slice(1), palette[i]]]))
        };
    }
    applyTerminalTheme();
    terminal.open(host);
    window.addEventListener('monitor-theme-change', applyTerminalTheme);
    let connection = null;
    function disconnect(message) {
        if (connection) connection.close();
        connection = null;
        toggle.textContent = 'Reconnect terminal';
        status.textContent = message;
    }
    function connect() {
        terminal.reset();
        status.textContent = 'Connecting to nvtop…';
        toggle.textContent = 'Disconnect terminal';
        connection = new EventSource('/nvtop/stream?columns=' + columns);
        connection.addEventListener('ready', () => {
            status.textContent = 'Live · read-only';
        });
        connection.addEventListener('output', event => {
            const bytes = Uint8Array.from(atob(JSON.parse(event.data)), c => c.charCodeAt(0));
            terminal.write(bytes);
        });
        connection.addEventListener('finished', event => disconnect(JSON.parse(event.data).message));
        connection.onerror = () => disconnect('Connection lost. Reconnect to start a new terminal session.');
    }
    toggle.addEventListener('click', () => connection ? disconnect('Disconnected · terminal output is frozen') : connect());
    window.addEventListener('pagehide', () => disconnect('Disconnected'));
    window.addEventListener('pageshow', event => { if (event.persisted) connect(); });
    connect();
})();
