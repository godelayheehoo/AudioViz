import unittest
import numpy as np
import pygame
from src.render.pygame_render import PyGameRenderer

class TestOscilloscopeRender(unittest.TestCase):
    def setUp(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        self.renderer = PyGameRenderer()
        self.renderer.mode = 'wave'

    def test_waveform_points_type(self):
        """
        Reproduce TypeError: points must be number pairs
        """
        # Create dummy audio chunk (1024, 2)
        audio_chunk = np.random.rand(1024, 2).astype(np.float32)
        
        try:
            self.renderer._render_waveform(audio_chunk)
        except TypeError as e:
            self.fail(f"Oscilloscope rendering failed with TypeError: {e}")
        except Exception as e:
            self.fail(f"Oscilloscope rendering failed with unexpected error: {e}")

if __name__ == '__main__':
    import os
    unittest.main()
