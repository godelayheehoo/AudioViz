# Live Audio Streaming Guide

Your AudioViz project now supports **live audio input**! You can stream audio from your microphone, the PCM1808 ADC, or any other audio input device.

---

## Quick Start

### List Available Audio Devices

First, find out which audio devices are available:

```bash
python src/main.py --list-devices
```

This will show all audio input devices with their IDs and capabilities.

### Run with Live Audio (Default Device)

Use your system's default microphone/input:

```bash
python src/main.py --live
```

### Run with Specific Device

Use a specific audio device by ID or name:

```bash
# By device ID (from --list-devices output)
python src/main.py --live --device 0

# By ALSA device name (on Raspberry Pi)
python src/main.py --live --device hw:0,0
```

### Run with File (Original Behavior)

Play from a file (this is still the default):

```bash
# Uses default example file
python src/main.py

# Use specific file
python src/main.py --file path/to/your/audio.wav
```

---

## Raspberry Pi Setup

On your Pi with the PCM1808 ADC:

1. **Check available devices:**
   ```bash
   python src/main.py --list-devices
   ```

2. **Find your PCM1808 device** - it will likely be:
   - Device ID `0` (if it's the only/primary input)
   - Or named something like `snd_rpi_googlevoicehat_soundcard`

3. **Run with the PCM1808:**
   ```bash
   # Try default first
   python src/main.py --live
   
   # Or specify explicitly
   python src/main.py --live --device hw:0,0
   ```

---

## Command-Line Reference

```
python src/main.py [OPTIONS]

Options:
  --live              Use live audio input instead of file playback
  --device DEVICE     Audio input device (ID number or name like 'hw:0,0')
  --file PATH         Path to audio file for playback (default mode)
  --list-devices      Show all available audio input devices and exit
  -h, --help          Show help message
```

---

## Examples

### Desktop Testing (Microphone)

```bash
# List devices
python src/main.py --list-devices

# Use default mic
python src/main.py --live

# Use specific device (e.g., USB mic is device 2)
python src/main.py --live --device 2
```

### Raspberry Pi with PCM1808

```bash
# Standard ALSA device
python src/main.py --live --device hw:0,0

# Or by device ID (usually 0)
python src/main.py --live --device 0
```

### Auto-start on Boot

Update your systemd service to use live audio:

```ini
[Service]
ExecStart=/home/pi/audio_viz/venv/bin/python /home/pi/audio_viz/src/main.py --live --device hw:0,0
```

---

## Troubleshooting

### "No audio device found" Error

Try explicitly listing devices:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Audio Latency/Glitching

1. **Reduce chunk size** in `src/config.py`:
   ```python
   CHUNK_SIZE = 512  # Lower = less latency, more CPU
   ```

2. **Disable other processes** consuming audio on the Pi

3. **Check CPU usage** - Pi Zero 2 is limited

### Wrong Device Selected

Use `--list-devices` to see all devices, then specify the correct one:
```bash
python src/main.py --list-devices
python src/main.py --live --device <correct_id>
```

### Buffer Overflow Warnings

If you see "Audio buffer overflow" warnings:
- **Increase chunk size** in config
- **Lower FFT size** to reduce processing load
- **Reduce visualization complexity** (lower resolution, etc.)

---

## Performance Tips for Raspberry Pi

1. **Start simple** - Test with default settings first
2. **Monitor CPU** - Use `htop` to check load
3. **Adjust config** - Lower `FFT_SIZE`, `WINDOW_WIDTH`, and `FPS` if needed
4. **Use framebuffer** - Avoid X11 overhead with `SDL_VIDEODRIVER=fbcon`
5. **Kill background services** - Disable Bluetooth, WiFi if not needed

---

## Technical Details

### Audio Pipeline

```
PCM1808 → I2S → ALSA → sounddevice → LiveAudioSource → DSPPipeline → Renderer
```

### Configuration

Audio settings are defined in `src/config.py`:
- **SAMPLE_RATE**: 44100 Hz (adjustable, but match your hardware)
- **CHUNK_SIZE**: 1024 samples (~23ms at 44.1kHz)
- **CHANNELS**: 2 (stereo)

### Sample Rate Considerations

- **44.1kHz**: Standard audio, good balance
- **48kHz**: Professional audio, what PCM1808 typically uses
- **96kHz**: High-resolution (requires more processing power)

If your PCM1808 is configured for 48kHz, update `src/config.py`:
```python
SAMPLE_RATE = 48000
```

---

Enjoy your live audio visualization! 🎵📊
