"""Languages can drive the system around them.

The runner gives your program a real subprocess, so shelling out works
exactly as it would outside the IDE.

    nishachar run examples/system_commands.py
"""
import platform
import subprocess
import sys

print(f"python  {sys.version.split()[0]}")
print(f"os      {platform.system()} {platform.release()}")

result = subprocess.run(
    [sys.executable, "-c", "print('spawned a child process')"],
    capture_output=True,
    text=True,
)
print(f"child   {result.stdout.strip()!r} (exit {result.returncode})")
