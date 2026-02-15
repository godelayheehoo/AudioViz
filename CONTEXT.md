# Project Plan: Real-Time Audio Spectrum Display (Python → Raspberry Pi Zero 2 WH)
## 1. Overall Goal

Build a real-time audio spectrum visualization system that:

- Accepts stereo line-level audio input

- Performs real-time FFT analysis

- Renders a visually clean spectrum display

- Runs on a Raspberry Pi Zero 2 WH

- Uses a small HDMI display

- Captures audio via either:

  - PCM1808 I2S ADC, or

  - USB class-compliant audio interface

The system must:

- Run at 30–60 FPS

- Handle 44.1 kHz or 48 kHz audio

- Remain responsive on limited hardware

- Be structured cleanly so hardware dependencies are isolated

- Primary development will occur on Windows, with deployment to Raspberry Pi later.

## 2. Development Strategy Overview

We will:

- Develop and validate DSP + rendering pipeline entirely on Windows.

- Use file-based audio input during development.

- Abstract audio input layer to allow seamless switch to live ALSA input on Pi.

- Keep rendering backend adaptable (windowed during dev, framebuffer/SDL on Pi).

The objective is to minimize hardware iteration during early development.

## 3. Current Phase: Local Windows Development

This phase is the focus.

We are NOT:

- Handling GPIO

- Configuring I2S

- Debugging ALSA

- Optimizing for Pi yet

We ARE:

- Building DSP pipeline

- Building visualization engine

- Designing clean architecture

## 4. Antigravity Agent Guidelines

### Path Compatibility
- **ALWAYS use forward slashes (`/`) for file paths in terminal commands**, even on Windows.
  - Correct: `./venv/Scripts/python -m src.main`
  - Incorrect: `.\venv\Scripts\python -m src.main` (Backslashes are treated as escape characters in the git-bash/mingw shell env).

### Testing Mandate
- **ALWAYS create at least one unit test** for new logic or bug reproductions whenever viable.
  - If a feature is complex or buggy, create a reproduction script in `tests/` before fixing it.
  - Verify fixes by running the specific test.