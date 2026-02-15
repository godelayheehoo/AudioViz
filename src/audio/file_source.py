import numpy as np
import scipy.io.wavfile as wav
from scipy import signal
import os
from .base import AudioSource
from ..config import SAMPLE_RATE, CHUNK_SIZE

class FileAudioSource(AudioSource):
    """
    Audio source that reads from a file (WAV).
    """
    def __init__(self, file_path, loop=True):
        self.file_path = file_path
        self.loop = loop
        self.cursor = 0
        self.data = None
        self.fs = 0
        self._load_file()

    def _load_file(self):
        if not os.path.exists(self.file_path):
             # Create a silent buffer if file not found to avoid crash during dev
             print(f"Warning: Audio file not found at {self.file_path}. Using silence.")
             self.fs = SAMPLE_RATE
             self.data = np.zeros((SAMPLE_RATE * 5, 2), dtype=np.float32)
             return

        try:
            self.fs, data = wav.read(self.file_path)
            
            # Convert to float32 -1.0 to 1.0
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                 data = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.uint8:
                data = (data.astype(np.float32) - 128.0) / 128.0
            
            # Handle channels
            if len(data.shape) == 1:
                # Mono to Stereo
                data = np.stack((data, data), axis=1)
            
            # Resample if necessary
            if self.fs != SAMPLE_RATE:
                print(f"Resampling from {self.fs} to {SAMPLE_RATE} Hz...")
                num_samples = int(len(data) * SAMPLE_RATE / self.fs)
                data = signal.resample(data, num_samples)
                self.fs = SAMPLE_RATE
                
            self.data = data
            print(f"Loaded audio file: {self.file_path} ({len(self.data)/self.fs:.2f}s)")
            
        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.data = np.zeros((SAMPLE_RATE * 5, 2), dtype=np.float32)

    def start(self):
        self.cursor = 0

    def stop(self):
        pass

    def read_chunk(self) -> np.ndarray:
        if self.data is None:
            return np.zeros((CHUNK_SIZE, 2), dtype=np.float32)
            
        end = self.cursor + CHUNK_SIZE
        
        if end > len(self.data):
            if self.loop:
                # Wrap around
                chunk = self.data[self.cursor:]
                remaining = CHUNK_SIZE - len(chunk)
                chunk = np.concatenate((chunk, self.data[:remaining]))
                self.cursor = remaining
                return chunk
            else:
                # Pad with zeros
                chunk = self.data[self.cursor:]
                padding = np.zeros((CHUNK_SIZE - len(chunk), 2), dtype=np.float32)
                chunk = np.concatenate((chunk, padding))
                self.cursor = len(self.data) # Stay at end
                return chunk
        else:
            chunk = self.data[self.cursor:end]
            self.cursor = end
            return chunk
