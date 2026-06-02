#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from local_beta.app import run_server


ROOT = Path(__file__).resolve().parent
WATCH_PATTERNS = ("*.py", "*.css")


def watched_mtime() -> float:
    files = [Path(__file__)]
    for pattern in WATCH_PATTERNS:
        files.extend((ROOT / "local_beta").rglob(pattern))
    return max(path.stat().st_mtime for path in files if path.exists())


def run_with_reloader():
    env = os.environ.copy()
    env["EUDAMED_RELOAD_CHILD"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    command = [sys.executable, str(Path(__file__).resolve()), "--no-reload"]
    child = None
    last_mtime = 0.0
    opened_browser = False
    try:
        while True:
            current_mtime = watched_mtime()
            if child is None or child.poll() is not None:
                child = subprocess.Popen(command, cwd=str(ROOT), env=env)
                last_mtime = current_mtime
                if not opened_browser and not os.environ.get("EUDAMED_NO_BROWSER"):
                    opened_browser = True
                    time.sleep(0.6)
                    webbrowser.open("http://127.0.0.1:8765/")
            elif current_mtime > last_mtime:
                print("Code change detected. Restarting local beta...")
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
                child = subprocess.Popen(command, cwd=str(ROOT), env=env)
                last_mtime = current_mtime
            time.sleep(0.8)
    except KeyboardInterrupt:
        if child and child.poll() is None:
            child.send_signal(signal.SIGINT)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.terminate()


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        run_server()
    elif "--no-reload" in sys.argv or os.environ.get("EUDAMED_RELOAD_CHILD") == "1":
        run_server()
    else:
        run_with_reloader()
