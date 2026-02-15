import numpy as np
from ..config import SAMPLE_RATE, FFT_SIZE

class DSPPipeline:
    """
    Handles Digital Signal Processing (FFT) for audio data.
    """
    
    def __init__(self):
        self.window = np.hanning(FFT_SIZE)
        
    def process(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Compute the FFT of the audio chunk for both channels.
        
        Args:
            audio_chunk (np.ndarray): Input audio data (N, 2).
            
        Returns:
            np.ndarray: Frequency spectrum magnitude (2, N/2 + 1).
        """
        # Ensure we have enough data, pad if necessary
        if len(audio_chunk) < FFT_SIZE:
             padding = np.zeros((FFT_SIZE - len(audio_chunk), audio_chunk.shape[1]))
             audio_chunk = np.concatenate((audio_chunk, padding))
        
        # Process each channel
        # Channel 0 (Left)
        left_data = audio_chunk[:FFT_SIZE, 0] * self.window
        left_spectrum = np.abs(np.fft.rfft(left_data))
        
        # Channel 1 (Right)
        if audio_chunk.shape[1] > 1:
            right_data = audio_chunk[:FFT_SIZE, 1] * self.window
            right_spectrum = np.abs(np.fft.rfft(right_data))
        else:
            # Duplicate mono if only 1 channel
            right_spectrum = left_spectrum

        return np.vstack((left_spectrum, right_spectrum))
