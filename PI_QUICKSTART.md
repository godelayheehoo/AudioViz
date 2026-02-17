# Raspberry Pi Quick Start Guide

Quick reference for running the audio visualizer on your Raspberry Pi Zero 2 WH.

## Auto-Start Setup (Recommended)

The visualizer is configured to auto-start on boot using X11.

### Initial Setup

Run the setup script once:

```bash
cd ~/AudioViz
chmod +x setup_x11_autostart.sh
./setup_x11_autostart.sh
```

Then configure auto-login:

```bash
# Enable auto-login on tty1
sudo systemctl edit getty@tty1
```

Add these lines in the editor:

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin james --noclear %I $TERM
```

Save and exit (Ctrl+X, Y, Enter).

Add auto-start to bash profile:

```bash
cat >> ~/.bash_profile << 'EOF'

# Auto-start X and visualizer on tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
EOF
```

**Reboot to start:**

```bash
sudo reboot
```

The visualizer will now auto-start on boot and display on your monitor!

### Manual Start (for testing)

```bash
cd ~/AudioViz
source venv/bin/activate
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

## Managing the Auto-Started Visualizer

### Stop the Visualizer

```bash
# Kill the running visualizer
pkill -f "python -m src.main"
```

### Restart the Visualizer

```bash
# Reboot (cleanest method)
sudo reboot

# Or kill and let auto-login restart it
sudo pkill -u james
```

### Disable Auto-Start

Remove the auto-start from `.bash_profile`:

```bash
nano ~/.bash_profile
# Delete or comment out the startx section
```

## Troubleshooting

### Audio Not Responding

Test if hardware is capturing audio:

```bash
# Stop the visualizer first
pkill -f "python -m src.main"

# Record a test
arecord -D hw:0,0 -f S32_LE -r 48000 -c 2 -d 5 test.wav

# Copy to your computer and play it
scp james@raspberrypi.local:~/test.wav .
```

If you hear silence, check:
- Audio source is connected to PCM1808 input (LIN, RIN, GND)
- Audio source is playing and volume is up
- Solder joints on audio input connector
- PCM1808 may need input coupling capacitors

### "Device or resource busy"

The visualizer is already running (this is normal after auto-start):

```bash
# Stop it first
pkill -f "python -m src.main"

# Then run your command
arecord -D hw:0,0 -f S32_LE -r 48000 -c 2 -d 2 test.wav
```

### Display Not Showing

Check if X11 is running:

```bash
ps aux | grep X
```

Check for errors:

```bash
cat ~/.local/share/xorg/Xorg.0.log
```

## Auto-Start on Boot

See the main `RASPBERRY_PI_SETUP.md` for systemd service configuration.

## Display Modes

Once running, you can:
- Click the dropdown menu (top right) to change visualization modes
- Press **spacebar** to cycle through modes
- Press **ESC** or close window to exit
