"""
Configuration constants for the Audio Visualization project.
"""

# Audio Settings
SAMPLE_RATE = 48000  # PCM1808 runs at 48kHz
CHUNK_SIZE = 1024  # Number of audio frames per buffer
CHANNELS = 2       # Stereo input

# FFT Settings
FFT_SIZE = 2048    # Size of the FFT window (usually power of 2)
SMOOTHING = 0.5    # Exponential smoothing factor for visualization

# Rendering Settings
FPS = 60
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480  # Matching Pi display potentially
FULLSCREEN = False
