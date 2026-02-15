# Raspberry Pi Zero 2 WH Audio Visualization Setup Guide

Complete instructions for setting up the audio visualization project on a Raspberry Pi Zero 2 WH with a PCM1808 ADC board.

---

## Hardware Overview

**Board:** PCM1808 24-bit Stereo ADC
- **Interface:** I2S (Inter-IC Sound)
- **Sample Rate:** Up to 96kHz
- **Bit Depth:** 24-bit
- **SNR:** 105dB

---

## Table of Contents

1. [Hardware Connections](#hardware-connections)
2. [Raspberry Pi OS Setup](#raspberry-pi-os-setup)
3. [I2S Configuration](#i2s-configuration)
4. [Audio System Configuration](#audio-system-configuration)
5. [Software Installation](#software-installation)
6. [Testing & Verification](#testing--verification)
7. [Running the Visualizer](#running-the-visualizer)
8. [Troubleshooting](#troubleshooting)

---

## Hardware Connections

### PCM1808 to Raspberry Pi Zero 2 WH Pin Mapping

Connect the PCM1808 to your Pi's GPIO header as follows:

| PCM1808 Pin | Function | Pi Zero 2 WH GPIO | Physical Pin |
|-------------|----------|-------------------|--------------|
| BCK         | Bit Clock | GPIO 18 (PCM_CLK) | Pin 12 |
| LRCK        | LR Clock (Word Select) | GPIO 19 (PCM_FS) | Pin 35 |
| DATA/DOUT   | Data Out | GPIO 20 (PCM_DIN) | Pin 38 |
| SCK         | System Clock | GPIO 4 (GPCLK0) | Pin 7 |
| VDD         | Power (3.3V) | 3.3V | Pin 1 or 17 |
| GND         | Ground | GND | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

### Audio Input Connections

Connect your audio source to the PCM1808:
- **LINL / RINL**: Left/Right audio input (single-ended)
- Ensure input voltage doesn't exceed the module's specifications

### Important Notes

- The PCM1808 requires a master clock (MCLK). We'll use GPIO 4 to generate this.
- Ensure all ground connections are solid to minimize noise.
- Use short wires for I2S signals to reduce interference.

---

## Raspberry Pi OS Setup

### 1. Install Raspberry Pi OS

**Recommended:** Raspberry Pi OS Lite (64-bit) for better performance
- Download from [raspberrypi.com/software](https://www.raspberrypi.com/software/)
- Flash to microSD card using Raspberry Pi Imager
- Enable SSH during setup or create empty `ssh` file in boot partition

### 2. Initial Configuration

SSH into your Pi:
```bash
ssh pi@raspberrypi.local
# Default password: raspberry
```

Update the system:
```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Enable I2S in Boot Config

Edit the boot configuration:
```bash
sudo nano /boot/config.txt
```

Add/modify these lines:
```ini
# Enable I2S
dtparam=i2s=on

# Disable onboard audio (conflicts with I2S)
dtparam=audio=off

# Enable master clock on GPIO 4 (12.288 MHz for 48kHz audio)
dtoverlay=pwm,pin=4,func=4
```

**Important:** For the PCM1808, we need a device tree overlay. Add:
```ini
# PCM1808 I2S ADC
dtoverlay=i2s-mmap
dtoverlay=googlevoicehat-soundcard
```

> **Note:** The `googlevoicehat-soundcard` overlay works well with PCM1808-style ADCs. If this doesn't work, we'll create a custom overlay.

Reboot:
```bash
sudo reboot
```

---

## I2S Configuration

### 1. Verify I2S Device

After reboot, check if the I2S device is detected:
```bash
arecord -l
```

You should see something like:
```
card 0: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcard]
  Subdevice #0: subdevice #0
```

### 2. Alternative: Custom Device Tree Overlay (if needed)

If the Google Voice HAT overlay doesn't work, create a custom one:

```bash
sudo nano /boot/overlays/pcm1808-overlay.dts
```

Add this content:
```dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835";

    fragment@0 {
        target = <&i2s>;
        __overlay__ {
            status = "okay";
        };
    };

    fragment@1 {
        target-path = "/";
        __overlay__ {
            pcm1808_codec: pcm1808-codec {
                #sound-dai-cells = <0>;
                compatible = "ti,pcm1808";
                status = "okay";
            };
        };
    };

    fragment@2 {
        target = <&sound>;
        __overlay__ {
            compatible = "simple-audio-card";
            simple-audio-card,name = "pcm1808";
            status = "okay";

            simple-audio-card,format = "i2s";
            simple-audio-card,bitclock-master = <&dailink0_slave>;
            simple-audio-card,frame-master = <&dailink0_slave>;

            simple-audio-card,cpu {
                sound-dai = <&i2s>;
            };

            dailink0_slave: simple-audio-card,codec {
                sound-dai = <&pcm1808_codec>;
            };
        };
    };
};
```

Compile and use it:
```bash
sudo dtc -@ -I dts -O dtb -o /boot/overlays/pcm1808.dtbo /boot/overlays/pcm1808-overlay.dts
```

Then update `/boot/config.txt`:
```ini
dtoverlay=pcm1808
```

Reboot again.

---

## Audio System Configuration

### 1. Install ALSA Utilities

```bash
sudo apt install -y alsa-utils
```

### 2. Configure ALSA

Create/edit ALSA configuration:
```bash
nano ~/.asoundrc
```

Add:
```
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}

pcm.capture {
    type plug
    slave {
        pcm "hw:0,0"
        rate 48000
        channels 2
        format S24_LE
    }
}
```

### 3. Set Recording Levels

```bash
alsamixer
```

- Press F4 to view capture devices
- Use arrow keys to adjust levels
- Press Esc to exit

Or set via command line:
```bash
amixer -c 0 sset 'Capture' 80%
```

### 4. Test Audio Capture

Record a 5-second test:
```bash
arecord -D hw:0,0 -f S24_LE -r 48000 -c 2 -d 5 test.wav
```

Play it back (you'll need audio output configured or copy to another device):
```bash
aplay test.wav
```

---

## Software Installation

### 1. Install Python and Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system libraries for audio and graphics
sudo apt install -y \
    portaudio19-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libportmidi-dev \
    libasound2-dev
```

### 2. Clone/Copy Your Project

**Option A: Clone from Git**
```bash
cd ~
git clone <your-repo-url> audio_viz
cd audio_viz
```

**Option B: Copy via SCP** (from your development machine)
```bash
# On your Windows machine
scp -r C:\Users\James\projects\audio_viz pi@raspberrypi.local:~/
```

### 3. Create Virtual Environment

```bash
cd ~/audio_viz
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Install Additional Pi-Specific Dependencies

The Pi might need some extra packages:
```bash
pip install RPi.GPIO  # If you need GPIO control
```

---

## Testing & Verification

### 1. Test Audio Input with sounddevice

Create a quick test script:
```bash
python3 << 'EOF'
import sounddevice as sd
import numpy as np

# List available devices
print("Available audio devices:")
print(sd.query_devices())

# Test recording
print("\nRecording 2 seconds...")
fs = 48000
duration = 2
recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='float32')
sd.wait()

print(f"Recording shape: {recording.shape}")
print(f"Level (RMS): {np.sqrt(np.mean(recording**2)):.4f}")
print("Test successful!")
EOF
```

### 2. Verify I2S Data Flow

Check kernel messages for I2S:
```bash
dmesg | grep i2s
```

Check if audio is being captured:
```bash
cat /proc/asound/card0/pcm0c/sub0/status
```

---

## Running the Visualizer

### 1. Modify Audio Source (if needed)

Your current project uses file or sounddevice sources. Ensure the audio input device is correctly selected. You may need to update the audio source configuration.

Check current audio devices:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Note the device number for your PCM1808.

### 2. Configure for Headless Operation

Since the Pi Zero 2 WH will likely run headless initially, you have options:

**Option A: X11 Forwarding via SSH**
```bash
# SSH with X11 forwarding
ssh -X pi@raspberrypi.local
cd ~/audio_viz
source venv/bin/activate
python3 src/main.py
```

**Option B: Framebuffer (Direct Display)**

If you have a display connected directly:
```bash
# Set SDL to use framebuffer
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

cd ~/audio_viz
source venv/bin/activate
python3 src/main.py
```

**Option C: VNC Server**

Install VNC for remote desktop:
```bash
sudo apt install -y realvnc-vnc-server
sudo raspi-config
# Navigate to: Interface Options -> VNC -> Enable
```

Then connect via VNC client and run normally.

### 3. Run the Visualizer

```bash
cd ~/audio_viz
source venv/bin/activate
python3 src/main.py
```

### 4. Auto-Start on Boot (Optional)

Create a systemd service:
```bash
sudo nano /etc/systemd/system/audio-viz.service
```

Add:
```ini
[Unit]
Description=Audio Visualizer
After=sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/audio_viz
Environment="DISPLAY=:0"
Environment="SDL_VIDEODRIVER=fbcon"
ExecStart=/home/pi/audio_viz/venv/bin/python /home/pi/audio_viz/src/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-viz.service
sudo systemctl start audio-viz.service
```

Check status:
```bash
sudo systemctl status audio-viz.service
```

---

## Troubleshooting

### No Audio Device Detected

```bash
# Check if I2S is enabled
dtparam i2s
# Should show: i2s=on

# Check loaded modules
lsmod | grep snd

# Check device tree
dtoverlay -l

# Check dmesg for errors
dmesg | grep -i 'i2s\|sound\|audio'
```

### Audio Input Not Working

```bash
# Test with explicit device
arecord -D plughw:0,0 -f cd -d 5 test.wav

# Check ALSA configuration
cat /proc/asound/cards

# Verify I2S clocks
# You should see clock signals on BCK and LRCK pins with a scope/logic analyzer
```

### Performance Issues

The Pi Zero 2 WH has limited CPU. To optimize:

1. **Lower the resolution:**
   - Edit your config to use a smaller window size

2. **Reduce FFT size:**
   - Smaller FFT = less CPU usage

3. **Overclock (carefully):**
   ```bash
   sudo nano /boot/config.txt
   # Add:
   # arm_freq=1200
   # over_voltage=2
   ```

4. **Disable desktop environment:**
   Use framebuffer mode instead of X11

### PyGame Display Issues

If PyGame doesn't display:
```bash
# Try different video drivers
export SDL_VIDEODRIVER=directfb  # or fbcon, or x11
```

### sounddevice Can't Find Device

If sounddevice can't see the PCM1808:
```bash
# Force ALSA backend
export SD_ENABLE_ALSA=1

# Or in Python:
import sounddevice as sd
sd.default.device = 'hw:0,0'
```

---

## Touchscreen Setup

Most modern touchscreens for the Raspberry Pi (USB, DSI, or HDMI) will "just work" like a mouse on the desktop. However, for a dedicated visualizer, you'll likely want to run it without the desktop (framebuffer mode) to save CPU.

### 1. Hardware Connection
- **USB Touchscreens**: Connect the touch USB cable to the Pi's micro-USB data port.
- **DSI Screens**: Connect via ribbon cable.
- **HDMI Screens**: Connect HDMI for video AND the USB cable for the touch data.

### 2. Pygame & Touch Events
Pygame automatically translates touch events into mouse events. Your existing mouse-click logic in the `Dropdown` class will work without modification.

### 3. Running Headless (Framebuffer)
If you are running without a desktop (using `SDL_VIDEODRIVER=fbcon`), you might need to tell Pygame where to look for input:

```bash
# Set these environment variables before running
export SDL_MOUSEDRV=TSLIB
export SDL_MOUSEDEV=/dev/input/event0  # Verify with: ls /dev/input/
```

### 4. Hide Mouse Cursor
For a clean "kiosk" look, you can hide the cursor in `src/render/pygame_render.py` by adding `pygame.mouse.set_visible(False)` in `__init__`.

---

## Performance Tips

1. **Use 48kHz sample rate** - Well supported and good balance
2. **Disable Bluetooth** if not needed: `sudo systemctl disable bluetooth`
3. **Disable WiFi** if using ethernet: `sudo rfkill block wifi`
4. **Increase GPU memory** in `/boot/config.txt`: `gpu_mem=128`
5. **Use lite OS** - No desktop environment overhead
6. **Consider real-time kernel** for ultra-low latency (advanced)

---

## Additional Resources

- [Raspberry Pi I2S Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#i2s)
- [PCM1808 Datasheet](https://www.ti.com/lit/ds/symlink/pcm1808.pdf)
- [ALSA Documentation](https://www.alsa-project.org/wiki/Main_Page)
- [Device Tree Overlays](https://www.raspberrypi.com/documentation/computers/configuration.html#device-trees-overlays-and-parameters)

---

## Quick Start Summary

For experienced users, here's the condensed version:

```bash
# 1. Enable I2S in /boot/config.txt
echo "dtparam=i2s=on" | sudo tee -a /boot/config.txt
echo "dtoverlay=googlevoicehat-soundcard" | sudo tee -a /boot/config.txt
sudo reboot

# 2. Install dependencies
sudo apt install -y python3 python3-pip python3-venv alsa-utils \
    portaudio19-dev libsdl2-dev

# 3. Setup project
cd ~
# Copy or clone your project here
cd audio_viz
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Test audio
arecord -D hw:0,0 -f S24_LE -r 48000 -c 2 -d 5 test.wav

# 5. Run visualizer
export SDL_VIDEODRIVER=fbcon
python3 src/main.py
```

---

Good luck with your audio visualization project! 🎵📊
