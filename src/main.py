import time
import numpy as np
from src.config import CHUNK_SIZE
from src.audio.base import AudioSource
from src.dsp.pipeline import DSPPipeline
from src.render.pygame_render import PyGameRenderer

from src.audio.file_source import FileAudioSource


import argparse
from pathlib import Path

# Resolve default path relative to this script
# src/main.py -> project_root/example_files/test.wav
PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_AUDIO = PROJECT_ROOT / "example_files" / "une-adorable-petite-fille-debordante-dimagination-17858.wav"

def main():
    parser = argparse.ArgumentParser(description="Audio Visualization")
    parser.add_argument("--file", type=str, default=str(DEFAULT_AUDIO), help="Path to audio file (WAV)")
    args = parser.parse_args()
    
    audio_path = args.file

    # components
    # Start with a warning if file doesn't exist, FileAudioSource handles it gracefully by playing silence
    print(f"Starting visualization for: {audio_path}")
    audio = FileAudioSource(audio_path)
    dsp = DSPPipeline()
    renderer = PyGameRenderer()
    
    audio.start()
    
    try:
        while renderer.running:
            # 1. Acquire Audio
            data = audio.read_chunk()
            
            # 2. Process
            spectrum = dsp.process(data)
            
            # 3. Render
            renderer.render(spectrum, data)
            renderer.update()
            
    except KeyboardInterrupt:
        pass
    finally:
        audio.stop()
        print("Exiting...")

if __name__ == "__main__":
    main()
