"""Checks (and with --fix sets up) what SpriteCast needs, and says what each thing is for. Runs on any Python 3.9+, packages or not.

    python doctor.py                  what is there, what is missing, the python to use
    python doctor.py --fix            sets up what is missing: a venv in ~/.cache/spritecast/venv with the packages
    python doctor.py --fix --browser  also Playwright's Chromium (~150 MB) - only needed when there is no Chrome or Edge
    python doctor.py --fix --characters   also the cut-out model for characters (224 MB, once)

The last line is always `PYTHON=<path>`: the interpreter to run isoprop.py / charpipe.py with.
"""
import argparse, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQ = HERE.parent / 'requirements.txt'
VENV = Path.home() / '.cache' / 'spritecast' / 'venv'
VPY = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
NEED = [('numpy', 'numpy', 'image maths'), ('PIL', 'pillow', 'reading and writing pictures'),
        ('scipy', 'scipy', 'cutting out, filling holes, fitting'), ('playwright', 'playwright', 'drives the browser that renders the 3D guide')]
OPTIONAL = [('onnxruntime', 'onnxruntime', 'characters only: runs the AI cut-out (without it `finish` stops - SPRITECAST_KEY=white cuts by the paper\'s white instead, which loses white clothes)'),
            ('mediapipe', 'mediapipe', 'facecheck only: compares faces across characters (Python 3.9-3.12, pip install mediapipe)')]


def missing(py):
    code = 'import importlib.util as u, sys; print(",".join(m for m in sys.argv[1:] if u.find_spec(m) is None))'
    r = subprocess.run([str(py), '-c', code] + [m for m, _, _ in NEED + OPTIONAL], capture_output=True, text=True)
    return [m for m in r.stdout.strip().split(',') if m] if r.returncode == 0 else [m for m, _, _ in NEED + OPTIONAL]


def line(ok, what, why):
    print(f"  {'OK ' if ok else '-- '} {what:<26} {why}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fix', action='store_true'); ap.add_argument('--characters', action='store_true'); ap.add_argument('--browser', action='store_true')
    ap.add_argument('--inner', action='store_true', help=argparse.SUPPRESS); a = ap.parse_args()
    if sys.version_info < (3, 9): sys.exit(f'Python 3.9+ is needed (this is {sys.version.split()[0]})')
    py = Path(sys.executable)
    if not a.inner:
        gone = missing(py)
        need_gone = [m for m in gone if m in [n for n, _, _ in NEED]]
        if need_gone and VPY.exists(): py = VPY; gone = missing(py); need_gone = [m for m in gone if m in [n for n, _, _ in NEED]]
        wants_ort = a.characters and 'onnxruntime' in gone
        if (need_gone or wants_ort) and a.fix:
            if py != VPY:
                print(f'setting up a venv in {VENV} (this Python is left alone) ...', flush=True)
                if subprocess.run([sys.executable, '-m', 'venv', str(VENV)], capture_output=True).returncode != 0:
                    import shutil; shutil.rmtree(VENV, ignore_errors=True)
                    sys.exit('this Python cannot make a venv (Debian/Ubuntu leave it out): `sudo apt install python3-venv`, or run this with\n'
                             'another Python 3.9+ (python.org, conda, Homebrew) - nothing else is needed from it')
                py = VPY
            subprocess.run([str(py), '-m', 'pip', 'install', '-q', '--upgrade', 'pip'], check=False)
            subprocess.run([str(py), '-m', 'pip', 'install', '-q', '-r', str(REQ)], check=True)
        if py != Path(sys.executable):                   # the rest is checked inside the interpreter that has the packages
            sys.exit(subprocess.run([str(py), __file__, '--inner'] + (['--fix'] if a.fix else []) + (['--characters'] if a.characters else []) + (['--browser'] if a.browser else [])).returncode)
    gone = missing(py)
    print(f'SpriteCast setup - Python {sys.version.split()[0]} at {py}')
    print('packages:')
    for m, pkg, why in NEED + OPTIONAL: line(m not in gone, pkg, why)
    ok = not [m for m, _, _ in NEED if m in gone]
    print('browser (renders the 3D guide - free, on this computer):')
    br = None
    if 'playwright' not in gone:
        sys.path.insert(0, str(HERE)); import browser
        br = browser.which()
        if not br and a.fix and a.browser:
            print('  no Chrome or Edge found - fetching Playwright\'s Chromium (~150 MB) ...', flush=True)
            subprocess.run([str(py), '-m', 'playwright', 'install', 'chromium'], check=False); br = browser.which()
    line(bool(br), br or 'none - install Chrome, or run with --fix --browser (Chromium, ~150 MB)', 'Chrome, Edge or Playwright\'s Chromium - the first one found')
    ok = ok and bool(br)
    print('cut-out model (characters only):')
    mp = None
    if 'onnxruntime' not in gone:
        sys.path.insert(0, str(HERE)); import charlib
        mp = charlib.seg_model(fetch=False)
        if not mp and a.fix and a.characters: mp = charlib.seg_model()
    line(bool(mp), 'BiRefNet lite (224 MB)', str(mp) if mp else 'fetched by itself the first time a character is finished (or --fix --characters)')
    print('keys (set in the environment; never pasted into the chat):')
    for k, why in (('OPENAI_API_KEY', 'drawing - props and characters (about $0.07 a prop, ~$2.2 a walking character; ~$1.5 with "mirror": true)'),
                   ('TRIPO_API_KEY', 'characters: the 3D model and its rig and walk; props: an optional detailed model'),
                   ('MESHY_API_KEY', 'optional: characters\' 3D model by Meshy instead ("modeler": "meshy")')):
        line(bool(os.environ.get(k)), k, why)
    print('ready: guides and the free trial' + (' - and drawing' if os.environ.get('OPENAI_API_KEY') else ' (drawing needs OPENAI_API_KEY)') if ok
          else 'not ready: run with --fix')
    print(f'PYTHON={py}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
