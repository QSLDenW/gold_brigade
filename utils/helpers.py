# utils/helpers.py
import pygame

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 200, 100), hover_color=None, text_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or self._lighten_color(color)
        self.text_color = text_color
        self.hovered = False
    
    def _lighten_color(self, color):
        return tuple(min(255, c + 30) for c in color)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, screen, font=None):
        if font is None:
            font = pygame.font.SysFont('Arial', 24)
        
        # Draw button background
        pygame.draw.rect(screen, self.hover_color if self.hovered else self.color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
        
        # Draw button text
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class InputField:
    def __init__(self, x, y, width, height, default_text="", font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = default_text
        self.active = False
        self.font = font or pygame.font.SysFont('Arial', 24)
        self.color_inactive = (200, 200, 200)
        self.color_active = (0, 100, 255)
        self.text_color = (0, 0, 0)
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_key_event(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == pygame.K_RETURN:
            self.active = False
        elif event.unicode.isprintable():
            self.text += event.unicode
    
    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, screen):
        # Update cursor blink
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > 500:  # Blink every 500ms
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
        
        # Draw input box
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, color, self.rect, 2)
        
        # Draw text
        text_surf = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surf, (self.rect.x + 5, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
        
        # Draw cursor if active
        if self.active and self.cursor_visible:
            cursor_pos = self.rect.x + 5 + text_surf.get_width()
            cursor_top = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
            cursor_height = text_surf.get_height()
            pygame.draw.line(screen, self.text_color, (cursor_pos, cursor_top), 
                             (cursor_pos, cursor_top + cursor_height), 2)
    
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

def draw_text(screen, text, font, color, x, y, align="left"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if align == "left":
        text_rect.topleft = (x, y)
    elif align == "center":
        text_rect.midtop = (x, y)
    elif align == "right":
        text_rect.topright = (x, y)
    
    screen.blit(text_surface, text_rect)
    return text_rect