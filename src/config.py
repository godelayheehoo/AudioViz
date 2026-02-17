"""
Configuration constants for the Audio Visualization project.
Loads settings from config.toml if available, otherwise uses defaults.
"""

import tomllib
from pathlib import Path

# Default configuration values
DEFAULTS = {
    'audio': {
        'sample_rate': 48000,
        'chunk_size': 1024,
        'channels': 2,
    },
    'display': {
        'fps': 60,
        'window_width': 800,
        'window_height': 480,
        'fullscreen': False,
    },
    'visualization': {
        'fft_size': 2048,
        'smoothing_factor': 0.7,
        'max_decay': 0.995,
        'waveform_initial_max': 0.1,
    },
    'shuffle_mode': {
        'silence_threshold': 0.03,
        'enabled_by_default': False,
    },
    'waveform': {
        'max_history_cycles': 5,
    },
    'spectrogram': {
        'history_length': 100,
    },
    'particles': {
        'max_count': 400,
    },
    'terrain': {
        'history_depth': 40,
        'num_bins': 60,
    },
}

# Try to load config.toml from project root
config_path = Path(__file__).parent.parent / 'config.toml'
config = DEFAULTS.copy()

if config_path.exists():
    try:
        with open(config_path, 'rb') as f:
            loaded_config = tomllib.load(f)
            # Merge loaded config with defaults (loaded values override defaults)
            for section, values in loaded_config.items():
                if section in config:
                    config[section].update(values)
                else:
                    config[section] = values
        print(f"Loaded configuration from {config_path}")
    except Exception as e:
        print(f"Warning: Could not load config.toml: {e}")
        print("Using default configuration values")
else:
    print(f"config.toml not found at {config_path}, using defaults")

# Export all config values as module-level constants
# Audio Settings
SAMPLE_RATE = config['audio']['sample_rate']
CHUNK_SIZE = config['audio']['chunk_size']
CHANNELS = config['audio']['channels']

# Display Settings
FPS = config['display']['fps']
WINDOW_WIDTH = config['display']['window_width']
WINDOW_HEIGHT = config['display']['window_height']
FULLSCREEN = config['display']['fullscreen']

# Visualization Settings
FFT_SIZE = config['visualization']['fft_size']
SMOOTHING_FACTOR = config['visualization']['smoothing_factor']
MAX_DECAY = config['visualization']['max_decay']
WAVEFORM_INITIAL_MAX = config['visualization']['waveform_initial_max']

# Shuffle Mode Settings
SILENCE_THRESHOLD = config['shuffle_mode']['silence_threshold']
SHUFFLE_ENABLED_DEFAULT = config['shuffle_mode']['enabled_by_default']

# Waveform Settings
MAX_HISTORY_CYCLES = config['waveform']['max_history_cycles']

# Spectrogram Settings
SPECTROGRAM_HISTORY_LENGTH = config['spectrogram']['history_length']

# Particle Settings
MAX_PARTICLES = config['particles']['max_count']

# Terrain Settings
TERRAIN_HISTORY_DEPTH = config['terrain']['history_depth']
TERRAIN_NUM_BINS = config['terrain']['num_bins']

