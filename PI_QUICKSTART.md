# Raspberry Pi Quick Start Guide

Quick reference for running the audio visualizer on your Raspberry Pi Zero 2 WH.

## Running the Visualizer

### Option 1: Use the Helper Script (Recommended)

```bash
cd ~/AudioViz
chmod +x run_pi.sh
./run_pi.sh
```

This automatically:
- Sets up the framebuffer display
- Activates the virtual environment
- Runs with live audio from the PCM1808

### Option 2: Manual Command

```bash
cd ~/AudioViz
source venv/bin/activate
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0
python -m src.main --live --device hw:0,0
```

### Option 3: File Playback (Not Recommended on Pi Zero 2)

⚠️ **Warning:** File playback requires loading the entire file into memory, which can crash the Pi Zero 2 with limited RAM.

For testing only with small files:
```bash
python -m src.main --file example_files/small_file.wav
```

## Important Notes

### Always Use `python -m src.main`

❌ **Don't use:** `python src/main.py`  
✅ **Do use:** `python -m src.main`

The `-m` flag ensures Python treats `src` as a package and imports work correctly.

### Memory Limitations

The Pi Zero 2 has only **512MB RAM**. To avoid crashes:

1. **Use live audio** instead of file playback
2. **Reduce FFT size** if needed (edit `src/config.py`)
3. **Lower FPS** if performance is poor (edit `src/config.py`)

### Performance Optimization

If the visualizer is slow or choppy:

1. **Lower the resolution** in `src/config.py`:
   ```python
   WINDOW_WIDTH = 640
   WINDOW_HEIGHT = 360
   ```

2. **Reduce FFT size** in `src/config.py`:
   ```python
   FFT_SIZE = 1024  # or even 512
   ```

3. **Lower frame rate** in `src/config.py`:
   ```python
   FPS = 30  # or even 20
   ```

## Command Line Options

```bash
# List available audio devices
python -m src.main --list-devices

# Use live audio (default device)
python -m src.main --live

# Use specific audio device
python -m src.main --live --device hw:0,0

# Use file playback (small files only!)
python -m src.main --file path/to/audio.wav
```

## Troubleshooting

### "Killed" Error

This means the Pi ran out of memory. Solutions:
- Use `--live` instead of file playback
- Use a smaller audio file
- Reduce `FFT_SIZE` in config

### No Display Output

Try different SDL video drivers:
```bash
export SDL_VIDEODRIVER=directfb  # or x11
python -m src.main --live
```

### No Audio Input

Check the PCM1808 is detected:
```bash
arecord -l
```

Test recording:
```bash
arecord -D hw:0,0 -f S32_LE -r 48000 -c 2 -d 2 test.wav
```

### Import Errors

Make sure you're in the project directory and using `-m`:
```bash
cd ~/AudioViz
python -m src.main --live
```

## Auto-Start on Boot

See the main `RASPBERRY_PI_SETUP.md` for systemd service configuration.

## Display Modes

Once running, you can:
- Click the dropdown menu (top right) to change visualization modes
- Press **spacebar** to cycle through modes
- Press **ESC** or close window to exit
