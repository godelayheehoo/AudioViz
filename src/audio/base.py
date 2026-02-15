from abc import ABC, abstractmethod
import numpy as np

class AudioSource(ABC):
    """
    Abstract base class for audio input sources.
    """
    
    @abstractmethod
    def read_chunk(self) -> np.ndarray:
        """
        Read a chunk of audio data.
        
        Returns:
            np.ndarray: Audio data chunk of shape (CHUNK_SIZE, CHANNELS)
        """
        pass

    @abstractmethod
    def start(self):
        """Start the audio stream."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the audio stream."""
        pass
