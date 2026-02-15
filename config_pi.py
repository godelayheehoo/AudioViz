"""
Raspberry Pi Zero 2 WH Optimized Configuration

This configuration reduces memory usage and computational load
for the limited resources of the Pi Zero 2 (512MB RAM, 4-core ARM).
"""

# Audio Settings
SAMPLE_RATE = 44100
CHUNK_SIZE = 512      # Reduced from 1024 - less latency, less memory
CHANNELS = 2          # Stereo input

# FFT Settings
FFT_SIZE = 1024       # Reduced from 2048 - half the memory, faster processing
SMOOTHING = 0.6       # Slightly more smoothing for stability

# Rendering Settings
FPS = 30              # Reduced from 60 - half the CPU load
WINDOW_WIDTH = 800    # Match your display
WINDOW_HEIGHT = 480   # Match your display
FULLSCREEN = True     # Use fullscreen on Pi display

# Pi-Specific Optimizations
USE_LIVE_AUDIO = True  # Default to live audio instead of file playback
DEFAULT_DEVICE = "hw:0,0"  # PCM1808 I2S device
