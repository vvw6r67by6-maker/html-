#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path

TEMPLATE_SCRIPT = '''\
import webview
import sys
import os

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    html_path = get_resource_path('index.html')
    webview.create_window('My HTML App', html_path, width=1024, height=768)
    webview.start()

if __name__ == '__main__':
    main()
'''

def check_pyinstaller():
    if shutil.which('pyinstaller') is None:
        print("[Error] PyInstaller not found. Please install it: pip install pyinstaller")
        sys.exit(1)

def pack_html(html_path, output_exe=None):
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"[Error] HTML file does not exist: {html_path}")
        sys.exit(1)

    if output_exe is None:
        output_exe = html_path.stem + '.exe'
    output_exe = Path(output_exe).resolve()

    with tempfile.TemporaryDirectory(prefix='html2exe_') as tmpdir:
        tmpdir = Path(tmpdir)
        print(f"[Info] Temporary working directory: {tmpdir}")

        shutil.copy(html_path, tmpdir / 'index.html')
        script_path = tmpdir / 'app.py'
        script_path.write_text(TEMPLATE_SCRIPT, encoding='utf-8')

        cmd = [
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--name', output_exe.stem,
            '--add-data', f'index.html{os.pathsep}.',
            str(script_path)
        ]

        print("[Info] Running PyInstaller ...")
        result = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)

        if result.returncode != 0:
            print("[Error] PyInstaller packaging failed:")
            print(result.stderr)
            sys.exit(1)

        dist_dir = tmpdir / 'dist'
        generated_exe = dist_dir / (output_exe.stem + '.exe')
        if not generated_exe.exists():
            print("[Error] Generated EXE file not found")
            sys.exit(1)

        shutil.move(str(generated_exe), str(output_exe))
        print(f"[Success] EXE generated: {output_exe}")

if __name__ == '__main__':
    # If no arguments are provided, enter interactive mode
    if len(sys.argv) == 1:
        print("No command line arguments detected, entering interactive mode:")
        html_input = input("Enter HTML file path: ").strip()
        if not html_input:
            print("No path entered, exiting.")
            sys.exit(1)
        output_input = input("Enter output EXE filename (press Enter to use default name): ").strip()
        sys.argv = [sys.argv[0], html_input] + ([output_input] if output_input else [])
    
    parser = argparse.ArgumentParser(description='Package an HTML file into a standalone EXE')
    parser.add_argument('html', help='Path to the input HTML file')
    parser.add_argument('output', nargs='?', help='Path to the output EXE file (optional)')
    args = parser.parse_args()

    check_pyinstaller()
    pack_html(args.html, args.output)