from abc import ABC, abstractmethod
import numpy as np

class Renderer(ABC):
    """
    Abstract base class for visualization renderers.
    """

    @abstractmethod
    def render(self, spectrum: np.ndarray, audio_chunk: np.ndarray = None):
        """
        Render the visualization frame.
        
        Args:
            spectrum (np.ndarray): Frequency data to visualize.
            audio_chunk (np.ndarray): Raw audio data (optional, for waveform).
        """
        pass

    @abstractmethod
    def update(self):
        """Handle window events and updates."""
        pass
