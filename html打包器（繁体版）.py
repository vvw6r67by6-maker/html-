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
        print("[錯誤] 未找到 PyInstaller，請先安裝：pip install pyinstaller")
        sys.exit(1)

def pack_html(html_path, output_exe=None):
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"[錯誤] HTML 檔案不存在: {html_path}")
        sys.exit(1)

    if output_exe is None:
        output_exe = html_path.stem + '.exe'
    output_exe = Path(output_exe).resolve()

    with tempfile.TemporaryDirectory(prefix='html2exe_') as tmpdir:
        tmpdir = Path(tmpdir)
        print(f"[資訊] 臨時工作目錄: {tmpdir}")

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

        print("[資訊] 正在執行 PyInstaller ...")
        result = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)

        if result.returncode != 0:
            print("[錯誤] PyInstaller 打包失敗：")
            print(result.stderr)
            sys.exit(1)

        dist_dir = tmpdir / 'dist'
        generated_exe = dist_dir / (output_exe.stem + '.exe')
        if not generated_exe.exists():
            print("[錯誤] 未找到生成的 EXE 檔案")
            sys.exit(1)

        shutil.move(str(generated_exe), str(output_exe))
        print(f"[成功] EXE 已生成: {output_exe}")

if __name__ == '__main__':
    # 如果未提供任何參數，則互動式詢問
    if len(sys.argv) == 1:
        print("未偵測到命令列參數，進入互動模式：")
        html_input = input("請輸入 HTML 檔案路徑: ").strip()
        if not html_input:
            print("未輸入路徑，退出。")
            sys.exit(1)
        output_input = input("請輸入輸出 EXE 檔案名稱（直接按 Enter 使用預設名稱）: ").strip()
        sys.argv = [sys.argv[0], html_input] + ([output_input] if output_input else [])
    
    parser = argparse.ArgumentParser(description='將 HTML 檔案打包為獨立的 EXE')
    parser.add_argument('html', help='輸入的 HTML 檔案路徑')
    parser.add_argument('output', nargs='?', help='輸出的 EXE 檔案路徑（可選）')
    args = parser.parse_args()

    check_pyinstaller()
    pack_html(args.html, args.output)
