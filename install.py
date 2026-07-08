#!/usr/bin/env python3
"""Universal installer — Windows/macOS/Linux. Installs the prestige CLI."""
import subprocess, sys
from pathlib import Path
def main():
    if sys.version_info < (3,11):
        sys.exit("Python 3.11+ required.")
    here = Path(__file__).resolve().parent
    r = subprocess.run([sys.executable,"-m","pip","install","-e","."], cwd=here)
    if r.returncode != 0:
        subprocess.run([sys.executable,"-m","pip","install","-e",".","--break-system-packages"], cwd=here)
    print("\n✓ prestige installed.")
    print("  prestige scaffold site.html   # premium starter")
    print("  prestige install claude       # wire into your agent (or: codex/opencode/cursor)")
    print("  prestige audit site.html      # verify against the five laws")
if __name__ == "__main__":
    main()
