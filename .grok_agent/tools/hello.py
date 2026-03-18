#!/usr/bin/env python3
import sys

print("🌟 Hello from .grok_agent/tools/hello.py!")
if len(sys.argv) > 1:
    print(f"Args: {' '.join(sys.argv[1:])}")
print("Global tool ready! 🚀")
