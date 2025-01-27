class Platform:
    def __init__(self, previous_platform=None, width = BASE_PLATFORM_WIDTH, height = 0):
        self.state = "normal"
        self.shake_timer = 0
        self.fall_speed = 0
        self.width = width
        self.height = height
        self.color = random.choice(["red", "blue"])
    
        
        if previous_platform:
            x = random.randint(0, SCREEN_WIDTH - width)
            y = previous_platform.rect.y - PLATFORM_SPACING
            self.rect = pygame.Rect(x, y, width, PLATFORM_HEIGHT)
        else:
            # Ground (initial) platform
            width = SCREEN_WIDTH
            x, y = 0, SCREEN_HEIGHT - 50
            self.rect = pygame.Rect(x, y, width, PLATFORM_HEIGHT)

    def update(self, dt):
        # If shaking or falling, move the platform
        if self.state == "shaking":
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.state = "falling"
                self.fall_speed = 3
        elif self.state == "falling":
            self.fall_speed += 0.2
            self.rect.y += self.fall_speed
        
    def render(self, screen, camera_offset, player, light_radius, dark_mode):
        
        player_pos = (player.rect.centerx, player.rect.centery - camera_offset)
        # Render the platform with it's color
        plat_screen_rect = self.rect.copy()
        plat_screen_rect.y -= camera_offset

        if dark_mode:
            # Loop over the platform's width to determine which parts are lit
            step = 5  # Granularity of the light check
            for x in range(plat_screen_rect.left, plat_screen_rect.right, step):
                for y in range(plat_screen_rect.top, plat_screen_rect.bottom, step):
                    dist_to_player = ((x - player_pos[0]) ** 2 + (y - player_pos[1]) ** 2) ** 0.5
                    if dist_to_player <= light_radius:
                        # Inside the light radius: draw real color
                        color = PLAYER_COLOR if self.color == "red" else PLATFORM_COLOR
                    else:
                        # Outside the light radius: draw gray
                        color = (128, 128, 128)

                    # Draw the pixel or small block
                    pygame.draw.rect(screen, color, (x, y, step, step))
        else:
            # Normal rendering (no dark mode)
            color = PLAYER_COLOR if self.color == "red" else PLATFORM_COLOR
            pygame.draw.rect(screen, color, plat_screen_rect)
            is_glowing = (self.color == player.color)
            if is_glowing:
                # Create a glowing effect by drawing an outer rectangle (larger and semi-transparent)
                glow_surface = pygame.Surface((plat_screen_rect.width + 10, plat_screen_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (255, 255, 255, 100), glow_surface.get_rect(), border_radius=8)
                screen.blit(glow_surface, (plat_screen_rect.x - 5, plat_screen_rect.y - 5))
            pygame.draw.rect(screen, color, plat_screen_rect, border_radius = 8)