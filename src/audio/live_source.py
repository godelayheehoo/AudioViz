import numpy as np
import sounddevice as sd
from .base import AudioSource
from ..config import SAMPLE_RATE, CHUNK_SIZE


class LiveAudioSource(AudioSource):
    """
    Audio source that captures live audio from a microphone or audio input device.
    Uses sounddevice for cross-platform audio capture.
    """
    
    def __init__(self, device=None, channels=2):
        """
        Initialize live audio source.
        
        Args:
            device: Device ID or name. None uses default input device.
                   On Pi, typically 'hw:0,0' or the device index.
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.device = device
        self.channels = channels
        self.stream = None
        self.buffer = np.zeros((CHUNK_SIZE, channels), dtype=np.float32)
        
    def start(self):
        """Start the audio input stream."""
        print(f"Starting live audio capture...")
        print(f"  Device: {self.device if self.device else 'default'}")
        print(f"  Sample rate: {SAMPLE_RATE} Hz")
        print(f"  Channels: {self.channels}")
        print(f"  Chunk size: {CHUNK_SIZE}")
        
        try:
            # Query device info
            if self.device is not None:
                device_info = sd.query_devices(self.device, 'input')
                print(f"  Device info: {device_info['name']}")
            
            # Open the audio stream
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                dtype='float32'
            )
            self.stream.start()
            print("Live audio stream started successfully!")
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            print("\nAvailable audio devices:")
            print(sd.query_devices())
            raise
    
    def stop(self):
        """Stop the audio input stream."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("Audio stream stopped.")
    
    def read_chunk(self) -> np.ndarray:
        """
        Read a chunk of audio data from the live stream.
        
        Returns:
            np.ndarray: Audio data chunk of shape (CHUNK_SIZE, channels)
        """
        if self.stream is None:
            return np.zeros((CHUNK_SIZE, self.channels), dtype=np.float32)
        
        try:
            # Read from stream
            data, overflowed = self.stream.read(CHUNK_SIZE)
            
            if overflowed:
                print("Warning: Audio buffer overflow detected!")
            
            return data
            
        except Exception as e:
            print(f"Error reading audio: {e}")
            return np.zeros((CHUNK_SIZE, self.channels), dtype=np.float32)


def list_audio_devices():
    """
    Utility function to list all available audio input devices.
    Useful for finding the correct device ID for your PCM1808.
    """
    print("Available Audio Input Devices:")
    print("=" * 80)
    
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"[{idx}] {device['name']}")
            print(f"    Max input channels: {device['max_input_channels']}")
            print(f"    Default sample rate: {device['default_samplerate']} Hz")
            print()


if __name__ == "__main__":
    # Run this directly to list available devices
    list_audio_devices()
