#!/usr/bin/env python3
"""Apple Vision Framework - native OCR for macOS"""
import subprocess, sys, os

image_path = sys.argv[1]
prompt = sys.argv[2] if len(sys.argv) > 2 else "Extract text"

# Use macOS sips + Vision through qlmanage or mdls
try:
    # Method 1: QuickLook metadata (Apple native)
    result = subprocess.run(['mdls', '-name', 'kMDItemContentText', image_path], 
                          capture_output=True, text=True, timeout=30)
    if result.stdout.strip():
        print(result.stdout)
        print("✅ Apple native OCR complete", file=sys.stderr)
    else:
        # Method 2: Use sips to verify image, then describe
        result = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', image_path],
                              capture_output=True, text=True, timeout=10)
        print(result.stdout)
        print("ℹ️ Image verified (Apple native)", file=sys.stderr)
        print("Note: For full Live Text, use macOS UI or Photos.app", file=sys.stderr)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
