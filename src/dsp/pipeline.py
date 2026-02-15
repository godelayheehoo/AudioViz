import numpy as np
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
             padding = np.zeros((FFT_SIZE - len(audio_chunk), audio_chunk.shape[1]))
             audio_chunk = np.concatenate((audio_chunk, padding))
        
        # Process each channel
        # Channel 0 (Left)
        left_data = audio_chunk[:FFT_SIZE, 0] * self.window
        left_fft = np.fft.rfft(left_data)
        left_spectrum = np.abs(left_fft)
        left_phase = np.angle(left_fft)
        
        # Channel 1 (Right)
        if audio_chunk.shape[1] > 1:
            right_data = audio_chunk[:FFT_SIZE, 1] * self.window
            right_fft = np.fft.rfft(right_data)
            right_spectrum = np.abs(right_fft)
            right_phase = np.angle(right_fft)
        else:
            # Duplicate mono if only 1 channel
            right_spectrum = left_spectrum
            right_phase = left_phase

        magnitude = np.vstack((left_spectrum, right_spectrum))
        phase = np.vstack((left_phase, right_phase))
        
        return magnitude, phase
