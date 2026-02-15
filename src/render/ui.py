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
