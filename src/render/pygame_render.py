import pygame
import pygame.surfarray
import numpy as np
from scipy.interpolate import make_interp_spline
from .base import Renderer
from .ui import Dropdown
from ..config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
import random
from collections import deque

class ParticleSystem:
    """Efficient particle system using numpy arrays for Raspberry Pi performance."""
    def __init__(self, max_particles=400):
        self.max_particles = max_particles
        # Particle properties stored as numpy arrays for efficiency
        self.positions = np.zeros((max_particles, 2), dtype=np.float32)  # x, y
        self.velocities = np.zeros((max_particles, 2), dtype=np.float32)  # vx, vy
        self.sizes = np.zeros(max_particles, dtype=np.float32)
        self.colors = np.zeros((max_particles, 3), dtype=np.uint8)  # r, g, b
        self.lifetimes = np.zeros(max_particles, dtype=np.float32)
        self.ages = np.zeros(max_particles, dtype=np.float32)
        self.active = np.zeros(max_particles, dtype=bool)
        self.particle_count = 0
    
    def spawn(self, x, y, vx, vy, size, color, lifetime):
        """Spawn a new particle if there's room."""
        # Find first inactive particle
        inactive_indices = np.where(~self.active)[0]
        if len(inactive_indices) == 0:
            return  # No room for new particles
        
        idx = inactive_indices[0]
        self.positions[idx] = [x, y]
        self.velocities[idx] = [vx, vy]
        self.sizes[idx] = size
        self.colors[idx] = color
        self.lifetimes[idx] = lifetime
        self.ages[idx] = 0.0
        self.active[idx] = True
        self.particle_count += 1
    
    def update(self, dt=1/60.0):
        """Update all active particles."""
        if self.particle_count == 0:
            return
        
        # Get active particles mask
        active_mask = self.active
        
        # Update positions
        self.positions[active_mask] += self.velocities[active_mask] * dt
        
        # Apply simple drag/friction
        self.velocities[active_mask] *= 0.98
        
        # Update ages
        self.ages[active_mask] += dt
        
        # Kill old particles
        dead_mask = self.ages >= self.lifetimes
        newly_dead = active_mask & dead_mask
        self.active[newly_dead] = False
        self.particle_count -= np.sum(newly_dead)
    
    def draw(self, surface):
        """Draw all active particles to the surface."""
        if self.particle_count == 0:
            return
        
        active_mask = self.active
        active_indices = np.where(active_mask)[0]
        
        for idx in active_indices:
            x, y = self.positions[idx]
            size = self.sizes[idx]
            color = tuple(self.colors[idx])
            
            # Fade based on age
            life_ratio = 1.0 - (self.ages[idx] / self.lifetimes[idx])
            alpha = int(255 * life_ratio)
            faded_color = tuple(int(c * life_ratio) for c in color)
            
            # Draw particle as circle
            if 0 <= x < WINDOW_WIDTH and 0 <= y < WINDOW_HEIGHT:
                pygame.draw.circle(surface, faded_color, (int(x), int(y)), max(1, int(size)))


class PyGameRenderer(Renderer):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Audio Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.running = True
        self.mode = 'bars' # 'bars', 'line', 'spectrogram', 'wave'
        
        # Dropdown menu for mode selection
        dropdown_options = ["Spectrum Bars", "Spectrum Curves", "Spectrogram", "Oscilloscope", "Radial Spectrum", "Radial Curves", "Phase Clock", "Particle Field", "Spectral Terrain"]
        self.mode_map = {
            "Spectrum Bars": "bars",
            "Spectrum Curves": "line",
            "Spectrogram": "spectrogram",
            "Oscilloscope": "wave",
            "Radial Spectrum": "radial",
            "Radial Curves": "radial_curves",
            "Phase Clock": "phase_clock",
            "Particle Field": "particles",
            "Spectral Terrain": "terrain"
        }
        dropdown_width = 200
        dropdown_height = 40
        dropdown_x = WINDOW_WIDTH - dropdown_width - 10
        dropdown_y = 10
        self.dropdown = Dropdown(
            dropdown_x, dropdown_y, dropdown_width, dropdown_height,
            dropdown_options,
            self.font,
            selected_idx=0,
            callback=self._on_mode_select
        )
        
        # Scale control dropdown (top left)
        scale_options = ["Automatic", "0.5x", "1x", "2x", "5x", "10x"]
        self.scale_values = {
            "Automatic": None,  # None means use adaptive normalization
            "0.5x": 0.5,
            "1x": 1.0,
            "2x": 2.0,
            "5x": 5.0,
            "10x": 10.0
        }
        scale_dropdown_width = 150
        scale_dropdown_height = 40
        scale_dropdown_x = 10
        scale_dropdown_y = 10
        self.scale_dropdown = Dropdown(
            scale_dropdown_x, scale_dropdown_y, scale_dropdown_width, scale_dropdown_height,
            scale_options,
            self.font,
            selected_idx=0,  # Default to Automatic
            callback=self._on_scale_select
        )
        self.scale_multiplier = None  # None = automatic
        
        # Spectrogram setup
        self.spectrogram_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.spectrogram_surf.fill((0, 0, 0))
        # Precompute colormaps for stereo channels
        self.colormap_left = self._generate_colormap_cyan()   # Cyan for left
        self.colormap_right = self._generate_colormap_magenta()  # Magenta for right
        
        # Adaptive normalization & Smoothing
        self.running_max = 1.0  # Track maximum spectrum value
        self.max_decay = 0.995  # Decay factor for running max (slower decay = smoother)
        self.waveform_max = 0.1  # Track maximum waveform amplitude (start small)
        self.smoothed_spectrum = None
        self.smoothing_factor = 0.7  # 0.0 = no smoothing, 0.9 = very slow/smooth
        
        # Particle system setup
        self.particle_system = ParticleSystem(max_particles=400)  # Conservative for RPi
        self.particle_trail_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.particle_trail_surf.fill((0, 0, 0))
        self.particle_trail_surf.set_alpha(255)
        
        # Spectral terrain setup
        self.terrain_history_left = deque(maxlen=40)  # Store last 40 FFT frames
        self.terrain_history_right = deque(maxlen=40)
        self.terrain_num_bins = 60  # Number of frequency bins to display

    def _on_mode_select(self, idx, option_name):
        """Callback when user selects a mode from dropdown"""
        self.mode = self.mode_map[option_name]
    
    def _on_scale_select(self, idx, option_name):
        """Callback when user selects a scale from dropdown"""
        self.scale_multiplier = self.scale_values[option_name]
    
    def _normalize_spectrum(self, spectrum: np.ndarray) -> np.ndarray:
        """
        Adaptively normalize spectrum based on running maximum,
        or use manual scale if set.
        """
        # If manual scale is set, use it instead of automatic
        if self.scale_multiplier is not None:
            return spectrum * self.scale_multiplier
        
        # Otherwise use automatic normalization
        # Get current max
        current_max = np.max(spectrum)
        
        # Update running max
        if current_max > self.running_max:
            self.running_max = current_max
        else:
            # Slowly decay the running max
            self.running_max *= self.max_decay
            # But don't let it get too small
            self.running_max = max(self.running_max, current_max * 0.5, 1.0)
        
        # Normalize
        if self.running_max > 0:
            return spectrum / self.running_max
        return spectrum
    
    def _apply_smoothing(self, spectrum: np.ndarray) -> np.ndarray:
        """
        Apply exponential moving average (EMA) smoothing to the spectrum.
        This reduces jitter and flicker in the visualization.
        """
        if self.smoothed_spectrum is None or self.smoothed_spectrum.shape != spectrum.shape:
            self.smoothed_spectrum = spectrum.copy()
            return spectrum
        
        # EMA: new_sm = factor * old_sm + (1 - factor) * current
        # Actually it's smoother if we say: 
        # smoothed = alpha * previous + (1 - alpha) * current
        self.smoothed_spectrum = (self.smoothing_factor * self.smoothed_spectrum + 
                                (1 - self.smoothing_factor) * spectrum)
        return self.smoothed_spectrum
    
    
    def _generate_colormap_cyan(self):
        """Generate cyan colormap: Black -> Dark Cyan -> Cyan -> Bright Cyan"""
        cmap = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            if i < 85:  # Dark cyan
                cmap[i] = (0, i * 3, i * 3)
            elif i < 170:  # Cyan
                cmap[i] = (0, 85*3 + (i-85)*2, 255)
            else:  # Bright cyan -> white
                cmap[i] = ((i-170)*3, 255, 255)
        return cmap
    
    def _generate_colormap_magenta(self):
        """Generate magenta colormap: Black -> Dark Magenta -> Magenta -> Bright Magenta"""
        cmap = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            if i < 85:  # Dark magenta
                cmap[i] = (i * 3, 0, i * 3)
            elif i < 170:  # Magenta
                cmap[i] = (255, 0, 85*3 + (i-85)*2)
            else:  # Bright magenta -> white
                cmap[i] = (255, (i-170)*3, 255)
        return cmap
    
    def _analyze_frequency_bands(self, spectrum):
        """
        Analyze frequency bands and return energy levels.
        Returns: (low_energy, mid_energy, high_energy) for each channel.
        """
        # Average across both channels for simplicity
        avg_spectrum = np.mean(spectrum, axis=0)
        
        # Define frequency bands (bin indices)
        # Low: 0-20 (~0-430 Hz) - bass
        # Mid: 21-100 (~430-2150 Hz) - midrange
        # High: 101-256 (~2150-5500 Hz) - treble
        low_energy = np.mean(avg_spectrum[0:21])
        mid_energy = np.mean(avg_spectrum[21:101])
        high_energy = np.mean(avg_spectrum[101:257])
        
        return low_energy, mid_energy, high_energy
    
    def _project_3d_to_2d(self, x, y, z, center_x, center_y, scale=1.0, camera_distance=300, tilt_angle=30):
        """
        Simple perspective projection from 3D to 2D with camera tilt.
        Args:
            x, y, z: 3D coordinates
            center_x, center_y: Screen center
            scale: Scaling factor
            camera_distance: Distance from camera (affects perspective)
            tilt_angle: Camera tilt angle in degrees (positive = looking down)
        Returns:
            (screen_x, screen_y)
        """
        # Apply rotation around X-axis to tilt the view downward
        # This gives a bird's-eye perspective
        angle_rad = np.radians(tilt_angle)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        # Rotate Y and Z coordinates
        y_rot = y * cos_a - z * sin_a
        z_rot = y * sin_a + z * cos_a
        
        # Simple perspective projection
        # The farther away (larger z), the smaller the object appears
        factor = camera_distance / (camera_distance + z_rot)
        screen_x = center_x + (x * scale * factor)
        screen_y = center_y - (y_rot * scale * factor)  # Negative because screen Y increases downward
        return int(screen_x), int(screen_y)

    def render(self, spectrum: np.ndarray, audio_chunk: np.ndarray = None, phase: np.ndarray = None):
        self.screen.fill((0, 0, 0)) # Clear screen
        
        if spectrum is None or len(spectrum) == 0:
            return
        
        # Normalize spectrum for better visualization across different audio files
        spectrum = self._normalize_spectrum(spectrum)
        
        # Apply temporal smoothing to reduce jitter
        spectrum = self._apply_smoothing(spectrum)

        if self.mode == 'bars':
            self._render_bars(spectrum)
        elif self.mode == 'line':
            self._render_line(spectrum)
        elif self.mode == 'spectrogram':
            self._render_spectrogram(spectrum)
        elif self.mode == 'wave':
            if audio_chunk is not None:
                self._render_waveform(audio_chunk)
        elif self.mode == 'radial':
            self._render_radial(spectrum)
        elif self.mode == 'radial_curves':
            self._render_radial_curves(spectrum)
        elif self.mode == 'phase_clock':
            if phase is not None:
                self._render_phase_clock(spectrum, phase)
        elif self.mode == 'particles':
            self._render_particle_field(spectrum)
        elif self.mode == 'terrain':
            self._render_spectral_terrain(spectrum)
            
        # Draw dropdowns
        self.scale_dropdown.draw(self.screen)
        self.dropdown.draw(self.screen)
        
        pygame.display.flip()

    def _render_spectrogram(self, spectrum):
        # spectrum: (2, N)
        # Scroll up: Move existing image up by 1 pixel
        self.spectrogram_surf.scroll(0, -1)
        
        # Determine width for each channel
        half_width = WINDOW_WIDTH // 2
        
        # We need to map spectrum bin magnitudes to colors
        # Limit to useful frequency range
        limit = spectrum.shape[1] // 2 
        
        for ch in range(2):
            data = spectrum[ch][:limit]
            
            # Resample data to fit half_width pixels
            # Simple linear interpolation or binning
            # For speed, let's just use simple binning/indexing
            indices = np.linspace(0, len(data)-1, half_width).astype(int)
            row_data = data[indices]
            
            # Normalize and map to 0-255
            # Logarithmic scaling usually looks better for audio
            row_data = np.log10(row_data + 1e-6) 
            row_data = (row_data + 3) / 4 # Approximate normalization range [-3, 1] to [0, 1]
            row_data = np.clip(row_data * 255, 0, 255).astype(int)
            
            # Convert to colors using channel-specific colormap
            # Creating a surface for this thin line (1px high)
            # Efficient way: create a buffer of pixels
            
            colormap = self.colormap_left if ch == 0 else self.colormap_right
            colors = colormap[row_data]  # shape (half_width, 3)
            # Fix broadcasting error: reshape to (width, height, 3)
            colors = colors.reshape(-1, 1, 3)
            
            # Create a 1px high line surface
            line_surf = pygame.Surface((half_width, 1))
            
            # Pygame surface locking for pixel access is slow in Python, 
            # but blitting an array is tricky without deps. 
            # Using pygame.surfarray is standard.
            pygame.surfarray.pixels3d(line_surf)[:] = colors
            
            # Blit index logic
            x_pos = 0 if ch == 0 else half_width
            self.spectrogram_surf.blit(line_surf, (x_pos, WINDOW_HEIGHT - 1))
            
            # Draw separator
            if ch == 0:
                pygame.draw.line(self.spectrogram_surf, (50, 50, 50), (half_width, 0), (half_width, WINDOW_HEIGHT))

        self.screen.blit(self.spectrogram_surf, (0, 0))

    def _render_bars(self, spectrum):
        # Spectrum shape is (2, N)
        num_channels = spectrum.shape[0]
        num_bins = spectrum.shape[1]
        
        bar_width = max(1, WINDOW_WIDTH // (num_bins // 4)) 
        
        colors = [(0, 255, 255), (255, 0, 255)] # Cyan for Left, Magenta for Right
        
        for ch in range(num_channels):
            for i in range(min(num_bins // 4, WINDOW_WIDTH // bar_width)):
                 height = min(WINDOW_HEIGHT, int(spectrum[ch][i] * WINDOW_HEIGHT * 0.9))
                 
                 # Offset bars slightly for visibility if overlapping, or just blend
                 # For now, simple overlay
                 x = i * bar_width
                 if ch == 1:
                     x += 2 # Slight offset for right channel
                     
                 # Draw with transparency simulation (not native in simple rect, so just lines or distinct rects)
                 # Converting to distinct rects
                 rect = (x, WINDOW_HEIGHT - height, bar_width - 1, height)
                 pygame.draw.rect(self.screen, colors[ch], rect, 1) # Outline for visibility overlay

    def _render_line(self, spectrum):
        # Spectrum shape is (2, N)
        num_channels = spectrum.shape[0]
        limit = spectrum.shape[1] // 4
        
        colors = [(0, 255, 255), (255, 0, 255)] # Cyan for Left, Magenta for Right

        for ch in range(num_channels):
            data = spectrum[ch][:limit]
            
            x = np.linspace(0, WINDOW_WIDTH, len(data))
            y = WINDOW_HEIGHT - np.clip(data * WINDOW_HEIGHT * 0.9, 0, WINDOW_HEIGHT)
            
            if len(x) > 3:
                try:
                    x_smooth = np.linspace(x.min(), x.max(), 300) 
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = spl(x_smooth)
                    y_smooth = np.clip(y_smooth, 0, WINDOW_HEIGHT)
                    points = list(zip(x_smooth, y_smooth))
                    
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, colors[ch], False, points, 2)
                except:
                    points = list(zip(x, y))
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, colors[ch], False, points, 2)
    
    def _render_radial(self, spectrum):
        """
        Render spectrum as radial bars emanating from a central circle,
        like a sunburst or circular equalizer.
        """
        # Spectrum shape is (2, N)
        num_channels = spectrum.shape[0]
        limit = spectrum.shape[1] // 4  # Use first quarter of spectrum bins
        
        # Center of the screen
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        # Inner circle radius (the "sun" in the middle)
        inner_radius = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 8
        
        # Maximum bar length
        max_bar_length = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 2 - inner_radius - 20
        
        # Total number of bars around the circle
        num_bars = min(limit, 120)  # Cap for performance and aesthetics
        
        # Colors for each channel
        colors = [(0, 255, 255), (255, 0, 255)]  # Cyan for Left, Magenta for Right
        
        # Draw inner circle
        pygame.draw.circle(self.screen, (50, 50, 50), (center_x, center_y), inner_radius, 2)
        
        # For each channel, we'll alternate bars around the circle
        # Or we can draw both channels with slight angle offset
        # Let's interleave them for a richer visual
        
        for i in range(num_bars):
            # Angle for this bar (distribute evenly around circle)
            angle = (2 * np.pi * i) / num_bars
            
            # Determine which channel to use (alternate)
            ch = i % num_channels
            
            # Get spectrum value for this bar
            bin_idx = int((i // num_channels) * (limit / (num_bars / num_channels)))
            bin_idx = min(bin_idx, limit - 1)
            magnitude = spectrum[ch][bin_idx]
            
            # Bar length based on magnitude
            bar_length = magnitude * max_bar_length * 0.9  # 0.9 to leave some margin
            
            # Calculate start and end points
            start_x = center_x + inner_radius * np.cos(angle)
            start_y = center_y + inner_radius * np.sin(angle)
            
            end_x = center_x + (inner_radius + bar_length) * np.cos(angle)
            end_y = center_y + (inner_radius + bar_length) * np.sin(angle)
            
            # Color interpolation based on magnitude for extra visual appeal
            # Blend between darker and lighter versions
            color_factor = min(1.0, magnitude * 1.5)
            color = tuple(int(c * (0.3 + 0.7 * color_factor)) for c in colors[ch])
            
            # Draw the bar as a line
            pygame.draw.line(self.screen, color, 
                           (int(start_x), int(start_y)), 
                           (int(end_x), int(end_y)), 
                           3)  # Line width

    def _render_radial_curves(self, spectrum):
        """
        Render spectrum as smooth radial curves emanating from a central circle.
        Uses spline interpolation in polar coordinates.
        Optimized for Raspberry Pi: uses bin averaging and reduced point count.
        """
        # Spectrum shape is (2, N)
        num_channels = spectrum.shape[0]
        limit = spectrum.shape[1] // 4  # Use first quarter of spectrum bins
        
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        inner_radius = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 8
        max_curve_reach = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 2 - 20
        
        # SUBSTANTIAL IMPROVEMENT: Use bin averaging for control points instead of just sampling.
        # This makes the "skeleton" much more stable.
        num_control_points = 18 # Enough for organic shapes, fewer = faster and smoother
        colors = [(0, 255, 255), (255, 0, 255)] # Cyan for Left, Magenta for Right
        
        # Draw base circle
        pygame.draw.circle(self.screen, (30, 30, 30), (center_x, center_y), inner_radius, 1)

        for ch in range(num_channels):
            # 1. Get stable control points by averaging bins
            data = spectrum[ch][:limit]
            
            # Simple bin averaging
            bin_size = len(data) // num_control_points
            magnitudes = []
            for i in range(num_control_points):
                chunk = data[i * bin_size : (i + 1) * bin_size]
                magnitudes.append(np.mean(chunk) if len(chunk) > 0 else 0)
            magnitudes = np.array(magnitudes)
            
            # 2. Setup angles
            angles = np.linspace(0, 2 * np.pi, num_control_points, endpoint=False)
            
            # Radii for control points
            radii = inner_radius + magnitudes * (max_curve_reach - inner_radius)
            
            # 3. Handle periodicity (closure)
            # scipy's periodic spline needs the first and last points to match
            radii_periodic = np.append(radii, radii[0])
            angles_periodic = np.append(angles, 2 * np.pi)
            
            # 4. Interpolation
            try:
                # 180 points is plenty for 800px display, and 2x faster than 360
                num_interp_points = 180 
                angles_fine = np.linspace(0, 2 * np.pi, num_interp_points)
                
                spl = make_interp_spline(angles_periodic, radii_periodic, k=3, bc_type='periodic')
                radii_fine = spl(angles_fine)
                
                # 5. Cartesian conversion - bulk calculation is faster
                cos_vals = np.cos(angles_fine)
                sin_vals = np.sin(angles_fine)
                x = center_x + radii_fine * cos_vals
                y = center_y + radii_fine * sin_vals
                
                points = list(zip(x.astype(int), y.astype(int)))
                
                if len(points) > 1:
                    pygame.draw.lines(self.screen, colors[ch], True, points, 2)
                    
            except Exception as e:
                # Minimal fallback
                x = center_x + radii * np.cos(angles)
                y = center_y + radii * np.sin(angles)
                points = list(zip(x.astype(int), y.astype(int)))
                if len(points) > 1:
                    pygame.draw.lines(self.screen, colors[ch], True, points, 2)
    
    def _render_phase_clock(self, spectrum, phase):
        """
        Render a radial "phase clock" where each frequency bin is a rotating vector.
        Vector length = magnitude, rotation angle = instantaneous phase.
        Creates a chaotic mechanical clock effect.
        """
        # Spectrum and phase shapes are (2, N)
        num_channels = spectrum.shape[0]
        
        # Use a reasonable number of bins for visual clarity
        # Too many = cluttered, too few = not enough detail
        num_bins = 80  # Sweet spot for clock-like appearance
        limit = min(spectrum.shape[1] // 4, num_bins * 2)  # Use lower frequencies primarily
        
        # Center of screen
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        # Maximum vector length
        max_length = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 2 - 30
        
        # Draw a subtle center circle as anchor
        pygame.draw.circle(self.screen, (40, 40, 40), (center_x, center_y), 5, 0)
        
        # Colors for channels
        base_colors = [(0, 255, 255), (255, 0, 255)]  # Cyan, Magenta
        
        # Process each channel
        for ch in range(num_channels):
            mag_data = spectrum[ch][:limit]
            phase_data = phase[ch][:limit]
            
            # Sample bins evenly
            indices = np.linspace(0, len(mag_data) - 1, num_bins).astype(int)
            magnitudes = mag_data[indices]
            phases = phase_data[indices]
            
            # Draw each bin as a rotating vector
            for i in range(num_bins):
                # Position angle around the circle (like clock tick marks)
                position_angle = (2 * np.pi * i) / num_bins
                
                # Add slight offset between channels for visibility
                if ch == 1:
                    position_angle += (np.pi / num_bins)  # Half-step offset
                
                # Vector length based on magnitude
                length = magnitudes[i] * max_length * 0.8
                
                # Rotation angle based on phase
                # Phase is in radians (-π to π), use it directly for rotation
                rotation = phases[i]
                
                # Combined angle: position + rotation from phase
                total_angle = position_angle + rotation
                
                # Calculate end point of vector
                end_x = center_x + length * np.cos(total_angle)
                end_y = center_y + length * np.sin(total_angle)
                
                # Color variation based on frequency (bin index)
                # Low frequencies (early bins) = warmer/dimmer
                # High frequencies (later bins) = cooler/brighter
                freq_factor = i / num_bins
                
                # Brightness based on magnitude
                brightness = min(1.0, magnitudes[i] * 2.0)
                
                # Interpolate color: low freq = dim, high freq = bright
                base_color = base_colors[ch]
                color = tuple(int(c * (0.3 + 0.7 * freq_factor) * (0.4 + 0.6 * brightness)) for c in base_color)
                
                # Line thickness varies slightly with magnitude for depth
                thickness = max(1, int(1 + brightness * 2))
                
                # Draw the vector from center to end point
                pygame.draw.line(self.screen, color,
                               (int(center_x), int(center_y)),
                               (int(end_x), int(end_y)),
                               thickness)



    def _render_particle_field(self, spectrum):
        """
        Render sound-reactive particle field driven by frequency bands.
        Low freq = heavy particles, mid freq = turbulence, high freq = sparks.
        """
        # Analyze frequency bands
        low_energy, mid_energy, high_energy = self._analyze_frequency_bands(spectrum)
        
        # Apply fade to trail surface for motion persistence
        # Fill with semi-transparent black to create trailing effect
        fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(25)  # Lower = longer trails, higher = faster fade
        self.particle_trail_surf.blit(fade_surface, (0, 0))
        
        # Center of screen for particle emission
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        # LOW FREQUENCY - Heavy, slow particles (bass)
        # Spawn rate based on bass energy
        bass_spawn_count = int(low_energy * 15)  # Scale appropriately
        for _ in range(bass_spawn_count):
            # Radial explosion from center
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(20, 60) * (1 + low_energy)
            vx = speed * np.cos(angle)
            vy = speed * np.sin(angle)
            
            # Large, slow particles
            size = random.uniform(4, 10) * (1 + low_energy * 0.5)
            lifetime = random.uniform(2.0, 4.0)
            
            # Cyan/Magenta base colors with variations
            # Alternate between channels for stereo effect
            channel = random.choice([0, 1])
            if channel == 0:  # Cyan channel
                # Darker, more saturated cyan for bass
                color_choice = (0, int(np.clip(150 + low_energy * 105, 0, 255)), int(np.clip(180 + low_energy * 75, 0, 255)))
            else:  # Magenta channel
                # Darker, more saturated magenta for bass
                color_choice = (int(np.clip(180 + low_energy * 75, 0, 255)), 0, int(np.clip(150 + low_energy * 105, 0, 255)))
            
            self.particle_system.spawn(center_x, center_y, vx, vy, size, color_choice, lifetime)
        
        # MID FREQUENCY - Turbulence and flow
        # Add turbulence to existing particles
        if self.particle_system.particle_count > 0:
            active_mask = self.particle_system.active
            turbulence_strength = mid_energy * 50
            
            # Add random velocity perturbations
            noise_x = np.random.uniform(-turbulence_strength, turbulence_strength, self.particle_system.max_particles)
            noise_y = np.random.uniform(-turbulence_strength, turbulence_strength, self.particle_system.max_particles)
            
            self.particle_system.velocities[active_mask, 0] += noise_x[active_mask]
            self.particle_system.velocities[active_mask, 1] += noise_y[active_mask]
        
        # Spawn some mid-range particles
        mid_spawn_count = int(mid_energy * 8)
        for _ in range(mid_spawn_count):
            # Random position variation
            x = center_x + random.uniform(-50, 50)
            y = center_y + random.uniform(-50, 50)
            
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(40, 100)
            vx = speed * np.cos(angle)
            vy = speed * np.sin(angle)
            
            size = random.uniform(2, 5)
            lifetime = random.uniform(1.0, 2.0)
            
            # Cyan/Magenta base colors with mid-tone brightness
            channel = random.choice([0, 1])
            if channel == 0:  # Cyan channel
                color_choice = (0, int(np.clip(200 + mid_energy * 55, 0, 255)), int(np.clip(220 + mid_energy * 35, 0, 255)))
            else:  # Magenta channel
                color_choice = (int(np.clip(220 + mid_energy * 35, 0, 255)), 0, int(np.clip(200 + mid_energy * 55, 0, 255)))
            
            self.particle_system.spawn(x, y, vx, vy, size, color_choice, lifetime)
        
        # HIGH FREQUENCY - Fast, bright sparks (treble)
        spark_spawn_count = int(high_energy * 20)
        for _ in range(spark_spawn_count):
            # Emit from random positions or edges
            if random.random() < 0.5:
                # From center
                x, y = center_x, center_y
            else:
                # From random edge
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                if edge == 'top':
                    x, y = random.uniform(0, WINDOW_WIDTH), 0
                elif edge == 'bottom':
                    x, y = random.uniform(0, WINDOW_WIDTH), WINDOW_HEIGHT
                elif edge == 'left':
                    x, y = 0, random.uniform(0, WINDOW_HEIGHT)
                else:
                    x, y = WINDOW_WIDTH, random.uniform(0, WINDOW_HEIGHT)
            
            # Fast, random direction
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(150, 300) * (1 + high_energy)
            vx = speed * np.cos(angle)
            vy = speed * np.sin(angle)
            
            # Small, short-lived
            size = random.uniform(1, 3)
            lifetime = random.uniform(0.2, 0.5)
            
            # Bright cyan/magenta sparks
            channel = random.choice([0, 1])
            brightness = int(np.clip(200 + high_energy * 55, 0, 255))
            if channel == 0:  # Bright cyan
                color_choice = (brightness // 2, 255, 255)
            else:  # Bright magenta
                color_choice = (255, brightness // 2, 255)
            
            self.particle_system.spawn(x, y, vx, vy, size, color_choice, lifetime)
        
        # Update particle physics
        self.particle_system.update(dt=1/60.0)
        
        # Draw particles to trail surface
        self.particle_system.draw(self.particle_trail_surf)
        
        # Blit trail surface to main screen
        self.screen.blit(self.particle_trail_surf, (0, 0))
    
    def _render_spectral_terrain(self, spectrum):
        """
        Render stereo spectral terrain as 3D wireframe landscapes.
        Frequency = X axis, Amplitude = Y axis, Time = Z axis (depth).
        """
        # Update terrain history buffers
        left_data = spectrum[0][:self.terrain_num_bins]
        right_data = spectrum[1][:self.terrain_num_bins]
        
        self.terrain_history_left.append(left_data.copy())
        self.terrain_history_right.append(right_data.copy())
        
        # Need at least 2 frames to draw terrain
        if len(self.terrain_history_left) < 2:
            return
        
        # Rendering parameters
        half_width = WINDOW_WIDTH // 2
        
        # Side-by-side layout
        # Left channel: left half, Right channel: right half
        channels_data = [
            (self.terrain_history_left, 0, half_width, (0, 255, 255)),  # Cyan
            (self.terrain_history_right, half_width, WINDOW_WIDTH, (255, 0, 255))  # Magenta
        ]
        
        for history, x_start, x_end, base_color in channels_data:
            center_x = (x_start + x_end) // 2
            center_y = WINDOW_HEIGHT // 2
            
            # Convert history deque to numpy array for easier manipulation
            # Reverse so newest data is farthest away (scrolls toward viewer)
            terrain_data = np.array(list(history))[::-1]  # Shape: (depth, num_bins)
            depth = len(terrain_data)
            
            # Scale factors
            x_scale = (x_end - x_start) / (self.terrain_num_bins + 1)
            y_scale = 150  # Amplitude scaling
            z_scale = 8    # Depth scaling
            
            # Draw wireframe
            # Draw horizontal lines (connecting frequency bins at same time/depth)
            for z_idx in range(depth):
                z = z_idx * z_scale
                
                # Brightness based on depth (farther = dimmer)
                depth_factor = 1.0 - (z_idx / depth) * 0.7
                color = tuple(int(c * depth_factor) for c in base_color)
                
                points = []
                for x_idx in range(self.terrain_num_bins):
                    x = (x_idx - self.terrain_num_bins // 2) * x_scale
                    y = terrain_data[z_idx][x_idx] * y_scale
                    
                    screen_x, screen_y = self._project_3d_to_2d(x, y, z, center_x, center_y, scale=1.0)
                    points.append((screen_x, screen_y))
                
                # Draw line connecting all points at this depth
                if len(points) > 1:
                    try:
                        pygame.draw.lines(self.screen, color, False, points, 1)
                    except:
                        pass  # Skip if points are out of bounds
            
            # Draw vertical lines (connecting same frequency across time/depth)
            # Draw fewer vertical lines for performance
            for x_idx in range(0, self.terrain_num_bins, 3):  # Every 3rd bin
                points = []
                for z_idx in range(depth):
                    z = z_idx * z_scale
                    x = (x_idx - self.terrain_num_bins // 2) * x_scale
                    y = terrain_data[z_idx][x_idx] * y_scale
                    
                    screen_x, screen_y = self._project_3d_to_2d(x, y, z, center_x, center_y, scale=1.0)
                    points.append((screen_x, screen_y))
                
                # Draw line connecting all points for this frequency
                if len(points) > 1:
                    # Use dimmer color for vertical lines
                    vert_color = tuple(int(c * 0.5) for c in base_color)
                    try:
                        pygame.draw.lines(self.screen, vert_color, False, points, 1)
                    except:
                        pass  # Skip if points are out of bounds
        
        # Draw center separator line
        pygame.draw.line(self.screen, (50, 50, 50), (half_width, 0), (half_width, WINDOW_HEIGHT), 1)

    def _render_waveform(self, audio_chunk):
        # audio_chunk shape (CHUNK_SIZE, 2)
        # We need to stabilize the waveform using a simple zero-crossing trigger on the Left channel
        
        trigger_idx = 0
        # Find rising edge zero crossing
        # Simple algorithm: look for where value goes from negative to positive
        left_channel = audio_chunk[:, 0]
        
        # Searching for crossing in first half of buffer to ensure we have enough to draw
        for i in range(len(left_channel) // 2):
            if left_channel[i] < 0 and left_channel[i+1] > 0:
                trigger_idx = i
                break
                
        # Draw length
        draw_len = min(len(audio_chunk) - trigger_idx, WINDOW_WIDTH)
        
        # We can map samples directly to X pixels if chunk size ~ window width
        # Or interpolate. 
        # Our CHUNK_SIZE is 1024, Window is 800. We can just pick 800 samples or resize.
        
        colors = [(0, 255, 255), (255, 0, 255)]
        
        # Determine scaling
        if self.scale_multiplier is not None:
            # Manual scaling: use fixed scale factor
            # For waveform, data is -1 to 1, so multiply by screen fraction
            scale = (WINDOW_HEIGHT / 2) * 0.8 * self.scale_multiplier
        else:
            # Adaptive scaling
            # Track max amplitude for adaptive scaling
            current_amp_max = np.max(np.abs(audio_chunk[trigger_idx : trigger_idx + draw_len, :]))
            if current_amp_max > self.waveform_max:
                self.waveform_max = current_amp_max
            else:
                self.waveform_max *= self.max_decay
                self.waveform_max = max(self.waveform_max, current_amp_max * 0.5, 0.01)
            
            # Scale factor - use more of the screen height
            scale = (WINDOW_HEIGHT / 2) * 0.8 / max(self.waveform_max, 0.01)
        
        for ch in range(2):
            data = audio_chunk[trigger_idx : trigger_idx + draw_len, ch]
            
            # X coordinates
            x = np.linspace(0, WINDOW_WIDTH, len(data))
            
            # Y coordinates: Center is height/2. Data is -1.0 to 1.0
            # Use adaptive scaling
            y = (WINDOW_HEIGHT / 2) - (data * scale)
            
            if ch == 1:
                # Offset Right channel slightly down or just color diff?
                # Let's offset Y slightly for visibility
                y += 2
            
            # Cast to int for pygame
            points = list(zip(x.astype(int), y.astype(int)))
            
            if len(points) > 1:
               pygame.draw.lines(self.screen, colors[ch], False, points, 2)

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Pass events to dropdowns
            self.dropdown.handle_event(event)
            self.scale_dropdown.handle_event(event)
            
            # Optional: Keep spacebar as a keyboard shortcut
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    modes = ['bars', 'line', 'spectrogram', 'wave', 'radial', 'radial_curves', 'phase_clock', 'particles', 'terrain']
                    mode_names = ["Spectrum Bars", "Spectrum Curves", "Spectrogram", "Oscilloscope", "Radial Spectrum", "Radial Curves", "Phase Clock", "Particle Field", "Spectral Terrain"]
                    current_idx = modes.index(self.mode)
                    next_idx = (current_idx + 1) % len(modes)
                    self.mode = modes[next_idx]
                    # Update dropdown to match
                    self.dropdown.selected_idx = next_idx
        self.clock.tick(FPS)
