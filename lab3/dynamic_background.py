import pygame
import sys
import random
import json
from pygame.locals import *

def load_settings():
    """Load game settings from settings.json"""
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

SETTINGS_FILE = "settings/settings.json"

# Load the settings
settings = load_settings()

GRADIENT_TOP_COLOR = list(map(int, settings["Colors"]["GRADIENT_TOP_COLOR"]))[:3]
GRADIENT_BOTTOM_COLOR = list(map(int, settings["Colors"]["GRADIENT_BOTTOM_COLOR"]))[:3]

class DynamicBackground:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.top_color = pygame.Color(GRADIENT_TOP_COLOR)  
        self.bottom_color = pygame.Color(GRADIENT_BOTTOM_COLOR)
        
        self.shapes = []
        for _ in range(90):
            self.shapes.append(BackgroundShape(screen_width, screen_height))

    def update(self, player_y, max_height, scroll_speed, camera_offset):
        # Gradually shift colors over time or based on player position
        y = player_y - camera_offset
        shift_factor = min(1, abs(y / max_height))

        # Interpolate the top color dynamically
        self.top_color.r = int(GRADIENT_TOP_COLOR[0] + (GRADIENT_BOTTOM_COLOR[0] - GRADIENT_TOP_COLOR[0]) * shift_factor)
        self.top_color.g = int(GRADIENT_TOP_COLOR[1] + (GRADIENT_BOTTOM_COLOR[1] - GRADIENT_TOP_COLOR[1]) * shift_factor)
        self.top_color.b = int(GRADIENT_TOP_COLOR[2] + (GRADIENT_BOTTOM_COLOR[2] - GRADIENT_TOP_COLOR[2]) * shift_factor)

        # Interpolate the bottom color dynamically
        self.bottom_color.r = int(GRADIENT_BOTTOM_COLOR[0] + (GRADIENT_TOP_COLOR[0] - GRADIENT_BOTTOM_COLOR[0]) * shift_factor)
        self.bottom_color.g = int(GRADIENT_BOTTOM_COLOR[1] + (GRADIENT_TOP_COLOR[1] - GRADIENT_BOTTOM_COLOR[1]) * shift_factor)
        self.bottom_color.b = int(GRADIENT_BOTTOM_COLOR[2] + (GRADIENT_TOP_COLOR[2] - GRADIENT_BOTTOM_COLOR[2]) * shift_factor)
        
        for shape in self.shapes:
            shape.update(scroll_speed)

    def render(self, screen):
        # Draw a vertical gradient
        for y in range(self.screen_height):
            # Interpolate color at each vertical pixel
            blend_factor = y / self.screen_height
            r = int(self.top_color.r + (self.bottom_color.r - self.top_color.r) * blend_factor)
            g = int(self.top_color.g + (self.bottom_color.g - self.top_color.g) * blend_factor)
            b = int(self.top_color.b + (self.bottom_color.b - self.top_color.b) * blend_factor)

            pygame.draw.line(screen, (r, g, b), (0, y), (self.screen_width, y))
        
        for shape in self.shapes:
            shape.render(screen)

class BackgroundShape:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.parallax_coef = random.uniform(0.1, 1.0)
        self.shape = random.choice(["circle", "square", "triangle"])  # Random shape type
        self.size = random.randint(10, 50)  # Random size
        self.x = random.randint(0, screen_width)  # Initial x position
        self.y = random.randint(-screen_height, 0)  # Initial y position
        self.color = (
            random.randint(50, 150),
            random.randint(50, 150), 
            random.randint(50, 150), 
            random.randint(100, 200),  # Semi-transparent
        )

    def update(self, scroll_distance):
        # Move shape downward, looping to the top if it exits the screen
        self.y += scroll_distance * self.parallax_coef
        if self.y > self.screen_height:
            self.y = random.randint(-self.screen_height, 0)  # Reset above screen
            self.x = random.randint(0, self.screen_width)  # New random x position

    def render(self, screen):
        if self.shape == "circle":
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size // 2)
        elif self.shape == "square":
            pygame.draw.rect(
                screen, self.color, (int(self.x - self.size // 2), int(self.y - self.size // 2), self.size, self.size)
            )
        elif self.shape == "triangle":
            pygame.draw.polygon(
                screen,
                self.color,
                [
                    (self.x, self.y - self.size // 2),  # Top
                    (self.x - self.size // 2, self.y + self.size // 2),  # Bottom-left
                    (self.x + self.size // 2, self.y + self.size // 2),  # Bottom-right
                ],
            )
    