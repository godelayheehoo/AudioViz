import pygame

class Dropdown:
    def __init__(self, x, y, width, height, options, font, selected_idx=0, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = font
        self.selected_idx = selected_idx
        self.callback = callback
        self.is_open = False
        
        # Colors
        self.color_bg = (30, 30, 30)
        self.color_bg_hover = (50, 50, 50)
        self.color_text = (200, 200, 200)
        self.color_border = (100, 100, 100)
        self.color_active = (0, 100, 200)

    def draw(self, screen):
        # Draw the main button (collapsed state)
        # Mouse hover check for main button
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        
        bg_color = self.color_bg_hover if is_hovered else self.color_bg
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, self.color_border, self.rect, 1)
        
        # Text
        text_surf = self.font.render(self.options[self.selected_idx], True, self.color_text)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
        # Draw arrow
        # Simple triangle
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery - 5),
            (self.rect.right - 15, self.rect.centery + 5)
        ]
        pygame.draw.polygon(screen, self.color_text, arrow_points)

        # Draw options if open
        if self.is_open:
            for i, option in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.height, self.rect.width, self.rect.height)
                
                # Highlight if hovered or selected
                is_opt_hovered = opt_rect.collidepoint(mouse_pos)
                if i == self.selected_idx:
                    opt_bg = self.color_active
                elif is_opt_hovered:
                    opt_bg = self.color_bg_hover
                else:
                    opt_bg = self.color_bg
                
                pygame.draw.rect(screen, opt_bg, opt_rect)
                pygame.draw.rect(screen, self.color_border, opt_rect, 1)
                
                opt_text = self.font.render(option, True, self.color_text)
                opt_text_rect = opt_text.get_rect(center=opt_rect.center)
                screen.blit(opt_text, opt_text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.is_open:
                    # Check if clicked on an option
                    for i, _ in enumerate(self.options):
                        opt_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.height, self.rect.width, self.rect.height)
                        if opt_rect.collidepoint(event.pos):
                            self.selected_idx = i
                            self.is_open = False
                            if self.callback:
                                self.callback(i, self.options[i])
                            return True
                    
                    # If clicked outside, close
                    # But if clicked on the main button, toggle (handled below? No, need to check here to prevent re-opening immediately if logic is simple)
                    if self.rect.collidepoint(event.pos):
                         self.is_open = not self.is_open # Toggle
                         return True
                    else:
                        self.is_open = False
                        return False # Pass through if clicked outside? Maybe return True to consume the click so it doesn't trigger other things?
                        # For now, let's say we consume it if it was open, effectively "closing" is the action.
                        return True
                else:
                    # Check if clicked on main button
                    if self.rect.collidepoint(event.pos):
                        self.is_open = True
                        return True
        return False


class ModeToggleButton:
    """Single circular toggle button that switches between bars and curves modes."""
    def __init__(self, x, y, radius, font, current_mode='bars', callback=None):
        """
        Args:
            x, y: Center position
            radius: Circle radius
            font: pygame font
            current_mode: 'bars' or 'curves' - the mode currently being displayed
            callback: Function to call when clicked (no arguments)
        """
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.font = font
        self.current_mode = current_mode
        self.callback = callback
        
        # Colors - translucent grey with white symbol
        self.color_bg = (60, 60, 60, 180)  # Translucent grey
        self.color_bg_hover = (80, 80, 80, 200)  # Slightly lighter on hover
        self.color_icon = (255, 255, 255)  # White icon
        self.color_border = (100, 100, 100, 200)
    
    def set_mode(self, mode):
        """Update the current mode being displayed."""
        self.current_mode = mode
    
    def draw(self, screen):
        """Draw the circular toggle button with current mode icon."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Check if mouse is hovering (circular hit detection)
        dx = mouse_pos[0] - self.center_x
        dy = mouse_pos[1] - self.center_y
        is_hovered = (dx * dx + dy * dy) <= (self.radius * self.radius)
        
        # Create a surface with alpha for translucency
        button_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        
        # Background color based on hover state
        bg_color = self.color_bg_hover if is_hovered else self.color_bg
        
        # Draw circle on the surface
        pygame.draw.circle(button_surf, bg_color, (self.radius, self.radius), self.radius)
        pygame.draw.circle(button_surf, self.color_border, (self.radius, self.radius), self.radius, 2)
        
        # Blit the translucent circle to screen
        screen.blit(button_surf, (self.center_x - self.radius, self.center_y - self.radius))
        
        # Draw icon based on current mode
        if self.current_mode == 'bars':
            # Draw three vertical bars (|||)
            bar_width = 2
            bar_height = 16
            spacing = 5
            
            for i in range(3):
                x = self.center_x - spacing + (i * spacing)
                y = self.center_y - bar_height // 2
                pygame.draw.rect(screen, self.color_icon, (x - bar_width // 2, y, bar_width, bar_height))
        
        elif self.current_mode == 'curves':
            # Draw wavy line (~~)
            import math
            wave_width = 20
            wave_height = 6
            num_points = 15
            
            points = []
            for i in range(num_points):
                t = i / (num_points - 1)
                x = self.center_x - wave_width // 2 + t * wave_width
                # Two complete sine waves
                y = self.center_y + wave_height * 0.5 * math.sin(t * 4 * math.pi)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(screen, self.color_icon, False, points, 2)
        
        elif self.current_mode == 'stream':
            # Draw single continuous wave (~) for streaming oscilloscope
            import math
            wave_width = 22
            wave_height = 7
            num_points = 20
            
            points = []
            for i in range(num_points):
                t = i / (num_points - 1)
                x = self.center_x - wave_width // 2 + t * wave_width
                # Single smooth sine wave
                y = self.center_y + wave_height * 0.5 * math.sin(t * 2 * math.pi)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(screen, self.color_icon, False, points, 2)
        
        elif self.current_mode == 'cycle':
            # Draw circular arrow (⟲) for cycle-locked oscilloscope
            import math
            # Draw a circular arc with an arrowhead
            arc_radius = 10
            arc_start = -0.3 * math.pi  # Start angle
            arc_end = 1.5 * math.pi     # End angle (almost full circle)
            num_points = 25
            
            # Draw arc
            points = []
            for i in range(num_points):
                t = i / (num_points - 1)
                angle = arc_start + t * (arc_end - arc_start)
                x = self.center_x + arc_radius * math.cos(angle)
                y = self.center_y + arc_radius * math.sin(angle)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(screen, self.color_icon, False, points, 2)
            
            # Draw arrowhead at the end
            arrow_angle = arc_end
            arrow_x = self.center_x + arc_radius * math.cos(arrow_angle)
            arrow_y = self.center_y + arc_radius * math.sin(arrow_angle)
            
            # Arrow direction (tangent to circle)
            arrow_dir = arrow_angle + math.pi / 2
            arrow_size = 4
            
            arrow_points = [
                (int(arrow_x), int(arrow_y)),
                (int(arrow_x - arrow_size * math.cos(arrow_dir + 0.4)), 
                 int(arrow_y - arrow_size * math.sin(arrow_dir + 0.4))),
                (int(arrow_x - arrow_size * math.cos(arrow_dir - 0.4)), 
                 int(arrow_y - arrow_size * math.sin(arrow_dir - 0.4)))
            ]
            pygame.draw.polygon(screen, self.color_icon, arrow_points)
    
    def handle_event(self, event):
        """Handle mouse events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Circular hit detection
                dx = event.pos[0] - self.center_x
                dy = event.pos[1] - self.center_y
                if (dx * dx + dy * dy) <= (self.radius * self.radius):
                    if self.callback:
                        self.callback()
                    return True
        return False
