#!/bin/bash
# Raspberry Pi Audio Visualizer Startup Script

# Navigate to script directory
cd "$(dirname "$0")"

# Check if user is in video group (needed for framebuffer access)
if ! groups | grep -q video; then
    echo "Adding user to video group for framebuffer access..."
    sudo usermod -a -G video $USER
    echo "Please log out and back in, then run this script again."
    exit 1
fi

# Ensure framebuffer is accessible
sudo chmod 666 /dev/fb0 2>/dev/null || true

# Set SDL to use framebuffer (for direct display without X11)
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0
export SDL_NOMOUSE=1

# Force ALSA backend for sounddevice
export SD_ENABLE_ALSA=1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run with live audio by default (use --file to override)
# Use python -m to ensure proper module imports
python -m src.main --live --device hw:0,0 "$@"
