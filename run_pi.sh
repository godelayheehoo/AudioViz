#!/bin/bash
# Raspberry Pi Audio Visualizer Startup Script

# Set SDL to use framebuffer (for direct display without X11)
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

# Force ALSA backend for sounddevice
export SD_ENABLE_ALSA=1

# Navigate to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run with live audio by default (use --file to override)
# Use python -m to ensure proper module imports
python -m src.main --live --device hw:0,0 "$@"
