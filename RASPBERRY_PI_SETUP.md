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

### Master Clock Generator (Si5351A)
The PCM1808 requires a precise 12.288 MHz master clock. The Raspberry Pi struggles to generate this cleanly, so we use an Si5351A I2C clock generator.

| Si5351A Pin | Function | Pi Zero 2 WH / PCM1808 Connection |
|-------------|----------|-----------------------------------|
| VIN / VCC   | Power    | Pi 3.3V (Pin 1 or 17) |
| GND         | Ground   | Pi GND (Pin 6, 9, etc.) |
| SDA         | I2C Data | Pi GPIO 2 (Pin 3) |
| SCL         | I2C Clock| Pi GPIO 3 (Pin 5) |
| CLK0 / Out0 | Clock Out| **PCM1808 SCK Pin** |

### PCM1808 to Raspberry Pi Pin Mapping

Connect the PCM1808 to your Pi's GPIO header as follows:

| PCM1808 Pin | Function | Connection |
|-------------|----------|------------|
| SCK         | System Clock | **Si5351A CLK0** |
| BCK         | Bit Clock | Pi GPIO 18 (Pin 12) |
| LRCK / LRC  | LR Clock (Word Select) | Pi GPIO 19 (Pin 35) |
| DATA/DOUT/OUT | Data Out | Pi GPIO 20 (Pin 38) |
| VDD / 3.3   | Power (3.3V) | Pi 3.3V |
| GND         | Ground | Pi GND |
| 5V / VCC    | Analog Power | **Pi 5V (Pin 2 or 4)** (Required!) |

### PCM1808 Format Pins (Master Mode)

To prevent clock drift between the Si5351A and the Raspberry Pi's internal clocks, the PCM1808 **must** act as the I2S Master. Connect the format pins on the breakout board as follows:

| PCM1808 Pin | Function | Connection |
|-------------|----------|------------|
| MD0 | Master/Slave Select | **3.3V** |
| MD1 | Master/Slave Select | **GND** |
| FMT | Audio Format (I2S)  | **GND** |

*(This configures the chip for Master Mode, 256fs, I2S Format)*

### Audio Input Connections

Connect your audio source to the PCM1808:
- **LINL / RINL**: Left/Right audio input (single-ended)
- Ensure input voltage doesn't exceed the module's specifications

### Important Notes

- Ensure all ground connections are solid to minimize noise.
- Use short wires for I2S and Clock signals to reduce interference.

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

### 3. Enable I2C and I2S Interfaces

**Step 3a: Enable I2C via raspi-config**
The Si5351A clock generator requires I2C to be explicitly enabled in the OS:
1. Run `sudo raspi-config`
2. Navigate to **Interface Options** -> **I2C**
3. Select **<Yes>** to enable the ARM I2C interface
4. Select **<Ok>**, then **<Finish>**

**Step 3b: Update Boot Config**
Edit the boot configuration to enable I2S and set the correct overlays:
```bash
sudo nano /boot/firmware/config.txt
```

Add/modify these lines:
```ini
# Enable I2C (required for Si5351A clock generator)
dtparam=i2c_arm=on

# Enable I2S
dtparam=i2s=on

# Disable onboard audio (conflicts with I2S)
dtparam=audio=off

# PCM1808 I2S ADC (Custom Overlay for Slave Mode)
dtoverlay=i2s-mmap
# We will compile the 'pcm1808' overlay in the next step
dtoverlay=pcm1808
```

> **Note:** We must use a custom overlay instead of the standard `googlevoicehat` overlay because the Pi must act as the I2S Slave to avoid clock drift.

Reboot:
```bash
sudo reboot
```

---

## I2S Configuration (Custom Device Tree Overlay)

Because the Si5351A Master Clock generator runs on a different physical crystal than the Raspberry Pi, the two devices will slowly drift out of sync. If the Pi generates the BCK/LRCK, the PCM1808 will detect this drift and infinitely mute its output (resulting in silence/empty `ff ff ff ff` captures).

To solve this, the PCM1808 is wired as the Hardware Master. We must configure the Pi to act as a Software Slave using a custom Device Tree Overlay.

### 1. Create the Custom Overlay

This overlay uses the `linux,spdif-dir` generic codec built into the kernel, which forces the Pi to act as a generic I2S "slave" capture device without needing the missing, specific PCM1808 driver perfectly compiled. 

```bash
sudo nano /boot/overlays/pcm1808-overlay.dts
```

Add this content exactly:
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
                compatible = "linux,spdif-dir";
                status = "okay";
            };
        };
    };

    fragment@2 {
        target-path = "/";
        __overlay__ {
            sound_pcm1808 {
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
};
```

### 2. Compile and Install
```bash
sudo dtc -@ -I dts -O dtb -o /boot/overlays/pcm1808.dtbo /boot/overlays/pcm1808-overlay.dts
```

*(You already added `dtoverlay=pcm1808` to `/boot/firmware/config.txt` in Step 3b).*

Reboot the Pi:
```bash
sudo reboot
```

### 2. Verify I2S Device

After reboot, check if the I2S device is detected:
```bash
arecord -l
```

You should see the `pcm1808` device listed as a capture hardware device.

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
```

### 3. PCM1808 Has No Mixer Controls

> **Important:** The PCM1808 is a simple ADC with **no software-controllable mixer controls**. This is normal behavior.
> 
> - Running `alsamixer` will show "This sound device does not have any controls"
> - Running `amixer` commands will fail with "Unable to find simple control"
> - **This is expected and not an error!**
> 
> The PCM1808's input gain is controlled by hardware (resistors on the board). If you need to adjust levels:
> - Adjust the output level of your audio source
> - Some PCM1808 modules have physical jumpers or trimpots for gain adjustment
> - Check your specific module's documentation for hardware gain controls


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
*(Note: `requirements.txt` now includes `adafruit-circuitpython-si5351` for the clock generator)*

### 5. Install Additional Pi-Specific Dependencies

The Pi might need some extra packages:
```bash
pip install RPi.GPIO  # If you need GPIO control
```

---

## Testing & Verification

### 1. Initialize Master Clock
Before ANY audio testing, the Si5351A must be running to provide the master clock.
```bash
cd ~/audio_viz
source venv/bin/activate
python rpi_setup/setup_clock.py
```
*(You should see "Success! Si5351A CLK0 is now generating 12.288 MHz")*

### 2. Test Audio Capture (ALSA)
Record a 5-second test from the hardware directly:
```bash
arecord -D hw:0,0 -f S32_LE -r 48000 -c 2 -d 5 test.wav
```

> **Note:** The PCM1808 on Raspberry Pi uses S32_LE format (24-bit audio in 32-bit containers), not S24_LE.

To quickly verify if actual audio was captured, inspect the file's raw bytes:
```bash
hexdump -C test.wav | head -n 20
```
If the output shows varying hex values (e.g., `a1 4f 33...`) after the WAV header, audio is being captured! If it only shows `00 00 00 00`, no audio data is being received (check clock and wiring).

### 3. Test Audio Input with sounddevice

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

⚠️ **Important:** The Pi Zero 2 has limited RAM (512MB). **Use live audio** instead of file playback to avoid memory issues.

**Recommended: Use the helper script**
```bash
cd ~/audio_viz
chmod +x run_pi.sh
./run_pi.sh
```

**Or run manually:**
```bash
cd ~/audio_viz
source venv/bin/activate
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

# Start master clock generator first
python rpi_setup/setup_clock.py

python -m src.main --live --device hw:0,0
```

> **Note:** Always use `python -m src.main` (not `python src/main.py`) to ensure proper module imports.

See `PI_QUICKSTART.md` for more options and troubleshooting.


### 4. Auto-Start on Boot (Recommended)

The best way to auto-start the visualizer on Raspberry Pi OS Lite is using auto-login with X11.

**Step 1: Run the setup script**

```bash
cd ~/audio_viz
chmod +x rpi_setup/setup_x11_autostart.sh
./rpi_setup/setup_x11_autostart.sh
```

**Step 2: Configure auto-login**

```bash
sudo systemctl edit getty@tty1
```

Add these lines:

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin james --noclear %I $TERM
```

Save and exit.

**Step 3: Add auto-start to bash profile**

```bash
cat >> ~/.bash_profile << 'EOF'

# Auto-start X and visualizer on tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
EOF
```

**Step 4: Reboot to activate**

```bash
sudo reboot
```

The visualizer will now auto-start on boot!

**To stop the auto-started visualizer:**

```bash
pkill -f "python -m src.main"
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
# Test with explicit device and correct format
arecord -D hw:0,0 -f S32_LE -r 48000 -c 2 -d 5 test.wav

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
   sudo nano /boot/firmware/config.txt
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

### Hardware Checks
Oscilloscope checks (in order of priority):

#### Si5351A Clock Output (most important first)
Probe Si5351A CLK0 (the wire going to PCM1808 SCK):

- You should see a clean 12.288 MHz square wave at ~3.3V amplitude. Verify frequency precisely — the PCM1808 is picky about this. Any significant deviation will cause garbled or no audio.
- Check for ringing or overshoot on edges. Long wires here are the enemy; if you see ugly edges, shorten the wire or add a small series resistor (22–33Ω) near the source.

#### I2S Bus Lines (BCK and LRCK)
These are driven by the Raspberry Pi once audio capture starts (arecord running):

- BCK (GPIO 18): Should be 3.072 MHz (= 48kHz × 64 bits per frame). This is the bit clock.
- LRCK (GPIO 19): Should be exactly 48kHz — a square wave that toggles between left and right channel. Easy to verify: it should be exactly 1/256th the frequency of the master clock.
- Trigger your scope on LRCK and verify BCK gives you exactly 32 cycles per LRCK half-period (for 32-bit frames in S32_LE mode).
    
#### DATA line (GPIO 20)
With audio playing into the PCM1808, you should see activity on the data line synchronized to BCK. With silence, it may be all zeros — that's fine. If you see random noise rather than clean synchronized transitions, something is wrong with the clock or power.

#### Power rails
Use the scope (or multimeter) to check for noise on 3.3V at the PCM1808 VDD pin. You want ripple under ~50mV. The Pi's 3.3V rail can be noisy; if audio is hummy or noisy, decoupling capacitors (100nF ceramic close to the PCM1808 power pins) can help.

#### Multimeter checks:

- Continuity on all ground connections between Pi, Si5351A, and PCM1808
- Confirm 3.3V is actually reaching the Si5351A VIN and PCM1808 VDD pins
- Check I2C pull-up resistors are present on SDA/SCL (should read ~3.3V at rest) — if the Si5351A isn't initializing, missing pull-ups are a common culprit   

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
4. **Increase GPU memory** in `/boot/firmware/config.txt`: `gpu_mem=128`
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
# 1. Enable I2S in /boot/firmware/config.txt
echo "dtparam=i2s=on" | sudo tee -a /boot/firmware/config.txt   
echo "dtoverlay=googlevoicehat-soundcard" | sudo tee -a /boot/firmware/config.txt
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
arecord -D hw:1,0 -f S32_LE -r 48000 -c 2 -d 5 test.wav

# 5. Run visualizer
export SDL_VIDEODRIVER=fbcon
python3 src/main.py
```

---

Good luck with your audio visualization project! 🎵📊
