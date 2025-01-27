class Player:
    def __init__(self, start_platform):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.bottom = start_platform.rect.top
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = True
        self.was_on_ground = True
        self.current_platform = start_platform
        self.past_platform = None
        self.max_floor = 0
        self.multi_jump = 0
        self.trail = []
        self.color = "red"
        self.rotation_angle = 0
        self.is_rotating = False
        
        self.current_trail_color = PLAYER_COLOR
        self.target_trail_color = PLAYER_COLOR
        self.color_change_timer = 0
        self.color_change_duration = 1
        
    def change_color(self):
        self.color = "blue" if self.color == "red" else "red"
        self.target_trail_color = PLATFORM_COLOR if self.color == "blue" else PLAYER_COLOR
        self.color_change_timer = self.color_change_duration  # Start transition

    def update(self, platforms, dt):
        self.velocity.y += GRAVITY * dt
        self.rect.y += self.velocity.y

        self.rect.x += self.velocity.x * dt

        # Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity.x *= -0.9
            
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.velocity.x *= -0.9

        self.on_ground = False
        for p in platforms:
            if self.velocity.y > 0 and self.rect.colliderect(p.rect):
                if self.color == p.color:
                    # Additional check: top landing
                    if (
                        self.rect.right > p.rect.left 
                        and self.rect.left < p.rect.right
                        and self.rect.bottom <= p.rect.top + self.velocity.y + 1
                    ):
                        self.rect.bottom = p.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                        
                        # Stop rotating when landing
                        if self.is_rotating:
                            self.is_rotating = False
                            self.rotation_angle = 0
                        
                        self.past_platform = self.current_platform
                        self.current_platform = p
                        if self.current_platform.height > self.max_floor:
                            self.max_floor = self.current_platform.height
                        self.multi_jump = self.current_platform.height - self.past_platform.height
                        break
                    
        if abs(self.velocity.y) >= 15:
            self.is_rotating = True 
                    
        if self.is_rotating:
            self.rotation_angle += 10 * dt
            self.rotation_angle %= 360
        self.update_trail()
        
        if self.color_change_timer > 0:
            self.color_change_timer -= dt/100
            blend_factor = 1 - (self.color_change_timer / self.color_change_duration)
            self.current_trail_color = self.lerp_color(self.current_trail_color, self.target_trail_color, blend_factor)
        
        just_landed = (self.on_ground and not self.was_on_ground)
        
        self.was_on_ground = self.on_ground
        
        return just_landed        
            
    def update_trail(self):
        # Add the current position to the trail
        self.trail.append((self.rect.centerx, self.rect.centery, self.color))
        # Limit the trail length based on speed
        total_speed = self.velocity.length()
        max_trail_length = int(total_speed ** 2)
        if len(self.trail) > max_trail_length:
            self.trail.pop(0)  # Remove the oldest position
            
    def lerp_color(self, color1, color2, t):
        return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))
            
    def render_trail(self, screen, camera_offset):
        for i, (x, y, color) in enumerate(reversed(self.trail)):
            alpha = max(255 - (i * 20), 0)
            trail_surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            rgb_color = PLAYER_COLOR if color == "red" else PLATFORM_COLOR
            pygame.draw.rect(trail_surface, (*rgb_color, alpha), trail_surface.get_rect(), border_radius=4)

            if self.is_rotating:
                trail_surface = pygame.transform.rotate(trail_surface, self.rotation_angle - (i * 10))
            trail_rect = trail_surface.get_rect(center=(x, y - camera_offset))
            screen.blit(trail_surface, trail_rect.topleft)

    
    def render(self, screen, camera_offset):
        # RENDER PLAYER
        self.render_trail(screen, camera_offset)
        player_screen_rect = self.rect.copy()
        player_screen_rect.y -= camera_offset
        player_color = PLAYER_COLOR if self.color == "red" else PLATFORM_COLOR
        # Render rotation
        if self.is_rotating:
            player_surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            # Draw a rectangle onto the surface
            pygame.draw.rect(player_surface, player_color, player_surface.get_rect(), border_radius=4)
            # Rotate the surface
            rotated_surface = pygame.transform.rotate(player_surface, self.rotation_angle)
            # Get the rotated rectangle's position
            rotated_rect = rotated_surface.get_rect(center=player_screen_rect.center)
            # Draw the rotated surface
            screen.blit(rotated_surface, rotated_rect.topleft)
        else:
            # Normal rendering - no rotation
            pygame.draw.rect(screen, player_color, player_screen_rect, border_radius = 4)
    
    def get_max_floor(self):
        return self.max_floor