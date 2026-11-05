"""The headless browser that renders the 3D guides (three.js, WebGL in software): an installed Chrome, else Edge (on every Windows),
else Playwright's own Chromium (`python -m playwright install chromium`, ~150 MB) - the first one there."""
ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']


def launch(pw):
    errors = []
    for channel in ('chrome', 'msedge', None):
        try: return pw.chromium.launch(channel=channel, args=ARGS) if channel else pw.chromium.launch(args=ARGS)
        except Exception as e: errors.append(f'{channel or "playwright chromium"}: {str(e).splitlines()[0]}')
    raise SystemExit('no browser to render with - install Google Chrome, or run `python -m playwright install chromium`\n  ' + '\n  '.join(errors))


def which():
    """the browser launch() would use, or None"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        for channel in ('chrome', 'msedge', None):
            try:
                b = pw.chromium.launch(channel=channel, args=ARGS) if channel else pw.chromium.launch(args=ARGS)
                v = b.version; b.close(); return f'{channel or "playwright chromium"} {v}'
            except Exception: pass
    return None
