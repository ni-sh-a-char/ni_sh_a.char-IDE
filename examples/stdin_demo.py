"""Reads standard input. Try:

    echo "Ada Lovelace" | nishachar run examples/stdin_demo.py

In the IDE, type into the Input tab before hitting Run.
"""
import sys

for line in sys.stdin:
    line = line.strip()
    if line:
        print(f"Hello, {line}!")
