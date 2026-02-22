import numpy as np
import scipy.fft
from ..config import SAMPLE_RATE, FFT_SIZE

class DSPPipeline:
    """
    Handles Digital Signal Processing (FFT) for audio data.
    """
    
    def __init__(self):
        self.window = np.hanning(FFT_SIZE)
        
    def process(self, audio_chunk: np.ndarray) -> tuple:
        """
        Compute the FFT of the audio chunk for both channels.
        
        Args:
            audio_chunk (np.ndarray): Input audio data (N, 2).
            
        Returns:
            tuple: (magnitude, phase) where:
                - magnitude (np.ndarray): Frequency spectrum magnitude (2, N/2 + 1)
                - phase (np.ndarray): Frequency spectrum phase (2, N/2 + 1)
        """
        # Ensure we have enough data, pad if necessary
        if len(audio_chunk) < FFT_SIZE:
             padding = np.zeros((FFT_SIZE - len(audio_chunk), audio_chunk.shape[1]), dtype=np.float32)
             audio_chunk = np.concatenate((audio_chunk, padding))
        
        # Take exactly FFT_SIZE samples
        data = audio_chunk[:FFT_SIZE, :]
        
        # Apply window to both channels simultaneously using broadcasting
        # data: (FFT_SIZE, channels), window: (FFT_SIZE,) -> (FFT_SIZE, 1)
        windowed_data = data * self.window[:, np.newaxis]
        
        # Perform real FFT along the time axis (axis=0) for all channels at once
        # scipy.fft is generally faster than numpy.fft, especially when scipy uses BLAS/LAPACK backends
        fft_result = scipy.fft.rfft(windowed_data, axis=0)
        
        # Calculate magnitude and phase
        # Result shape: (bins, channels) -> transpose to (channels, bins) to match old API
        spectrum = np.abs(fft_result).T
        phase = np.angle(fft_result).T
        
        # Handle mono fallback just in case
        if spectrum.shape[0] == 1:
            spectrum = np.vstack((spectrum, spectrum))
            phase = np.vstack((phase, phase))
            
        return spectrum, phase
