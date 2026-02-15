import unittest
import numpy as np
import pygame
from src.render.pygame_render import PyGameRenderer
from src.config import WINDOW_WIDTH, WINDOW_HEIGHT

class TestSpectrogramRender(unittest.TestCase):
    def setUp(self):
        # Initialize pygame headlessly for testing
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        self.renderer = PyGameRenderer()
        self.renderer.mode = 'spectrogram'

    def test_spectrogram_shape_broadcasting(self):
        """
        Reproduce the ValueError: could not broadcast input array 
        from shape (400,3) into shape (400,1,3)
        """
        # Create a dummy stereo spectrum
        # Shape (2, N) where N lets us map to width
        # Config has FFT_SIZE=2048, so spectrum length is 1025
        spectrum = np.random.rand(2, 1025)
        
        try:
            self.renderer._render_spectrogram(spectrum)
        except ValueError as e:
            self.fail(f"Spectrogram rendering failed with ValueError: {e}")
        except Exception as e:
            self.fail(f"Spectrogram rendering failed with unexpected error: {e}")

if __name__ == '__main__':
    import os
    unittest.main()
