import time
import numpy as np
from src.config import CHUNK_SIZE
from src.audio.base import AudioSource
from src.dsp.pipeline import DSPPipeline
from src.render.pygame_render import PyGameRenderer

from src.audio.file_source import FileAudioSource
from src.audio.live_source import LiveAudioSource, list_audio_devices


import argparse
from pathlib import Path

# Resolve default path relative to this script
# src/main.py -> project_root/example_files/test.wav
PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_AUDIO = PROJECT_ROOT / "example_files" / "une-adorable-petite-fille-debordante-dimagination-17858.wav"

def main():
    parser = argparse.ArgumentParser(description="Audio Visualization")
    parser.add_argument("--file", type=str, default=str(DEFAULT_AUDIO), help="Path to audio file (WAV)")
    parser.add_argument("--live", action="store_true", help="Use live audio input instead of file")
    parser.add_argument("--device", type=str, default=None, 
                        help="Audio input device (device ID, name, or 'hw:0,0'). Use --list-devices to see options.")
    parser.add_argument("--list-devices", action="store_true", help="List available audio input devices and exit")
    args = parser.parse_args()
    
    # List devices and exit if requested
    if args.list_devices:
        list_audio_devices()
        return
    
    # Determine audio source
    if args.live:
        # Live audio capture
        device = args.device
        
        # Convert device to int if it's a number
        if device is not None and device.isdigit():
            device = int(device)
        
        print(f"Starting live audio visualization...")
        audio = LiveAudioSource(device=device)
    else:
        # File playback
        audio_path = args.file
        print(f"Starting file visualization for: {audio_path}")
        audio = FileAudioSource(audio_path)
    
    dsp = DSPPipeline()
    renderer = PyGameRenderer()
    
    audio.start()
    
    try:
        while renderer.running:
            # 1. Acquire Audio
            data = audio.read_chunk()
            
            # 2. Process
            magnitude, phase = dsp.process(data)
            
            # 3. Render
            renderer.render(magnitude, data, phase)
            renderer.update()
            
    except KeyboardInterrupt:
        pass
    finally:
        audio.stop()
        print("Exiting...")

if __name__ == "__main__":
    main()
