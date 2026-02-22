# Audio Visualizer

Real-time audio spectrum visualization system designed for Raspberry Pi deployment with touchscreen interface.

## Features

### Visualization Modes
- **Spectrum Bars** - Frequency spectrum displayed as vertical bars
- **Spectrum Curves** - Smooth interpolated frequency curves  
- **Spectrogram** - Waterfall-style time-frequency display
- **Oscilloscope** - Stereo waveform with zero-crossing trigger

### Adaptive Scaling
- **Automatic Mode** - Dynamic normalization adapts to audio amplitude
- **Manual Scaling** - Fixed scale factors (0.5x, 1x, 2x, 5x, 10x)
- Separate scaling for all visualization modes

### Touch-Friendly UI
- **Mode Selector** (Top Right) - Switch between visualization types
- **Scale Control** (Top Left) - Toggle automatic/manual scaling
- Large 40px touch targets for touchscreen use
- Dark theme optimized for displays

## Current Status

**Development Phase:** Working prototype on Windows
- ✓ Real-time FFT processing for stereo audio
- ✓ Four visualization modes with adaptive normalization
- ✓ Touch-friendly dropdown UI system
- ✓ File-based audio playback (WAV)
- ✓ Automatic sample rate conversion

**Completed:** Raspberry Pi deployment
- ✓ I2S ADC integration (PCM1808 with Si5351A)
- ✓ ALSA audio input for live capture (hw:0,0)
- ✓ Framebuffer rendering optimization
- ✓ Hardware testing on Pi Zero 2 WH

## Installation

### Windows Development

1. **Clone the repository:**
```bash
git clone <repository-url>
cd audio_viz
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate environment:**
```bash
# Windows (bash/git-bash)
./venv/Scripts/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Raspberry Pi

> **Note:** Pi deployment is fully supported with real-time I2S audio capture and X11/Framebuffer rendering.

Hardware requirements:
- Raspberry Pi Zero 2 WH
- PCM1808 I2S ADC (for line-level stereo input)
- Si5351A Clock Generator module (essential for master clock generation)
- Small HDMI display (480x800 or similar)

## Usage

### Run Visualization

**Default audio file:**
```bash
./venv/Scripts/python -m src.main
```

**Custom audio file:**
```bash
./venv/Scripts/python -m src.main --file path/to/audio.wav
```

### Controls

- **Click Mode Dropdown** (top right) - Select visualization type
- **Click Scale Dropdown** (top left) - Choose scaling mode
- **Spacebar** - Quick toggle between visualization modes (keyboard shortcut)
- **Close Window** or **Ctrl+C** - Exit

## Architecture

```
src/
├── audio/           # Audio input abstraction
│   ├── base.py      # AudioSource interface
│   └── file_source.py  # File playback (development)
├── dsp/             # Digital Signal Processing
│   └── pipeline.py  # FFT computation
├── render/          # Visualization rendering
│   ├── base.py      # Renderer interface
│   ├── ui.py        # Dropdown UI component
│   └── pygame_render.py  # PyGame-based renderer
├── config.py        # Configuration constants
└── main.py          # Entry point

tests/               # Unit tests
example_files/       # Sample audio files
```

### Key Design Principles

1. **Hardware Abstraction** - Audio input and rendering are abstracted to enable platform portability
2. **Modular Pipeline** - Clean separation: Audio → DSP → Render
3. **Testable Components** - Each stage can be tested independently

## Configuration

Edit [`src/config.py`](src/config.py) to adjust parameters:

```python
# Audio Settings
SAMPLE_RATE = 44100   # Target sample rate
CHUNK_SIZE = 1024     # Audio buffer size
CHANNELS = 2          # Stereo

# FFT Settings  
FFT_SIZE = 2048       # FFT window size
SMOOTHING = 0.5       # Visualization smoothing

# Display Settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480   # Pi display size
FPS = 60              # Target frame rate
FULLSCREEN = False    # Set True for Pi deployment
```

## Raspberry Pi Deployment

### Hardware Setup

**Audio Input via I2S ADC:**
1. Connect PCM1808 to Pi GPIO (I2S pins)
2. Configure ALSA for I2S capture
3. Update `src/audio/` to use live ALSA input

**Alternative: USB Audio:**
1. Connect USB audio interface
2. Configure ALSA device
3. Update audio source configuration

### Software Setup

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pygame python3-numpy python3-scipy

# Install Python dependencies
pip3 install -r requirements.txt

# Configure audio device in config.py
# Set FULLSCREEN = True for kiosk mode
```

### Display Configuration

For headless operation with small HDMI display:
```bash
# /boot/config.txt
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=480 800 60 6 0 0 0  # Adjust to your display
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Visualization Modes

1. Implement rendering method in `PyGameRenderer`
2. Add mode to `mode_map` dictionary
3. Update dropdown options
4. Add corresponding tests

### Adding New Audio Sources

1. Subclass `AudioSource` in `src/audio/`
2. Implement `start()`, `read_chunk()`, `stop()`
3. Update `main.py` to use new source

## Performance Targets

- **Development (Windows):** 60 FPS @ 1024 chunk, 2048 FFT
- **Raspberry Pi Zero 2 WH:** 30+ FPS target with optimization
- **Latency:** < 50ms audio-to-display

## Dependencies

- **numpy** - Numerical processing
- **pygame** - Graphics rendering and UI
- **scipy** - FFT and signal processing
- **sounddevice** / **pyaudio** - Audio I/O (development)

## License

[Add your license here]

## Roadmap

- [x] Core DSP pipeline
- [x] Four visualization modes
- [x] Touch UI system
- [x] Adaptive normalization
- [x] I2S/ALSA audio input
- [x] Raspberry Pi optimization
- [x] Framebuffer rendering
- [x] Hardware testing
- [ ] Touchscreen calibration
- [x] Auto-start on boot

## Contributing

This is a personal Raspberry Pi project. Feel free to fork and adapt for your own use.

## Acknowledgments

Built with Python, PyGame, NumPy, and SciPy.
