import pygame
import sys
import random
from pygame.locals import *
import json
from dynamic_background import DynamicBackground, BackgroundShape

def load_settings():
    """Load game settings from settings.json"""
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

SETTINGS_FILE = "settings.json"

# Load the settings
settings = load_settings()

# Assign settings to variables
SCREEN_WIDTH = settings["Game World"]["SCREEN_WIDTH"]
SCREEN_HEIGHT = settings["Game World"]["SCREEN_HEIGHT"]
PLAYER_SIZE = settings["Game World"]["PLAYER_SIZE"]
PLATFORM_HEIGHT = settings["Game World"]["PLATFORM_HEIGHT"]
GRAVITY = settings["Physics"]["GRAVITY"]
BASE_JUMP = settings["Physics"]["BASE_JUMP"]
ACCELERATION = settings["Physics"]["ACCELERATION"]
FRICTION = settings["Physics"]["FRICTION"]
CAMERA_THRESHOLD = settings["Game World"]["CAMERA_THRESHOLD"]
PLATFORM_SPACING = settings["Game World"]["PLATFORM_SPACING"]
BASE_PLATFORM_WIDTH = settings["Game World"]["BASE_PLATFORM_WIDTH"]
MIN_PLATFORM_WIDTH = settings["Game World"]["MIN_PLATFORM_WIDTH"]
MAX_SPEED_LEVEL = settings["Game World"]["MAX_SPEED_LEVEL"]
PLATFORM_SHAKE_DURATION = settings["Game World"]["PLATFORM_SHAKE_DURATION"]
DIFICULTY_INCREASE_TIME = settings["Game World"]["DIFFICULTY_INCREASE_TIMER"]
PLATFORM_REDUCTION_COEF = settings["Game World"]["PLATFORM_REDUCTION_COEF"]
VERTICAL_SPEED_JUMP_INCREASE = settings["Physics"]["VERTICAL_SPEED_JUMP_INCREASE"]
COMBO_TIMEOUT = settings["Game World"]["COMBO_TIMEOUT"]
DARK_MODE_CHANCE = settings["Game World"]["DARK_MODE_CHANCE"]
DARK_MODE_DURATION = settings["Game World"]["DARK_MODE_DURATION"]
#WALL_BOUNCE_BACK = settings[""]

PLAYER_COLOR = list(map(int, settings["Colors"]["PLAYER_COLOR"]))[:3]
PLATFORM_COLOR = list(map(int, settings["Colors"]["PLATFORM_COLOR"]))[:3]


def create_light_mask(player_pos, radius = 20):
    light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    light_mask.fill((0, 0, 0, 220))  # Dark background with slight transparency

    # Draw a transparent circle (light) around the player
    pygame.draw.circle(light_mask, (0, 0, 0, 0), player_pos, radius)

    return light_mask

def calculate_light_radius(base_radius, combo):
    return base_radius + combo * 5

class GameState:
    def __init__(self):
        self.speed_level = 0
        self.base_speed = 0.5  # This will apply to forced scroll
        self.last_speed_increase = 0

        self.score = 0
        self.combo = 0
        self.combo_start_time = 0
        self.total_floors = 0
        self.platform_reduction_ratio = 1.0
        
        self.dark_mode = False
        self.light_radius = 100
        self.dark_mode_start_time = 0
        
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
            y = previous_platform.rect.y - PLATFORM_SPACING - random.randint(0, 20)
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
        
            # Draw a rounded rectangle onto the surface
            pygame.draw.rect(player_surface, player_color, player_surface.get_rect(), border_radius=4)
            
            # Rotate the surface
            rotated_surface = pygame.transform.rotate(player_surface, self.rotation_angle)
            
            # Get the rotated rectangle's position
            rotated_rect = rotated_surface.get_rect(center=player_screen_rect.center)
            
            # Blit (draw) the rotated surface
            screen.blit(rotated_surface, rotated_rect.topleft)
        else:
            # Normal rendering - no rotation
            pygame.draw.rect(screen, player_color, player_screen_rect, border_radius = 4)
    
    def get_max_floor(self):
        return self.max_floor

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    state = GameState()

    # Create initial platforms
    platforms = [Platform()]  # ground
    platforms[0].color = "red"
    for i in range(12):
        platforms.append(Platform(previous_platform=platforms[-1], height = i + 1))

    player = Player(platforms[0])
    top_floor = player.get_max_floor()
    
    camera_offset = 0
    previous_camera_offset = 0
    running = True
    
    background = DynamicBackground(SCREEN_WIDTH, SCREEN_HEIGHT)
        
    while running:
        dt_ms = clock.tick(60)
        dt = dt_ms / 16.67
        current_time = pygame.time.get_ticks()
        
        scroll_distance = previous_camera_offset - camera_offset
        previous_camera_offset = camera_offset
        
        background.update(player.rect.y, SCREEN_HEIGHT, scroll_distance)
        background.render(screen)
            
        # EVENTS
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if event.type == KEYDOWN and event.key == K_SPACE and player.on_ground:
                jump_power = BASE_JUMP * (1 + abs(player.velocity.x) * VERTICAL_SPEED_JUMP_INCREASE)
                player.velocity.y = jump_power
                player.on_ground = False # Prevents the player from being able to jump mid-air
                # Check for Combo
            elif event.type == KEYDOWN and event.key == K_LCTRL:
                player.change_color()
                 
        # INPUT ON GROUND
        keys = pygame.key.get_pressed()
        if player.on_ground:
            if keys[K_LEFT]:
                player.velocity.x -= ACCELERATION * dt
            if keys[K_RIGHT]:
                player.velocity.x += ACCELERATION * dt
            if player.velocity.x > 0:
                player.velocity.x -= FRICTION * dt
            elif player.velocity.x < 0:
                player.velocity.x += FRICTION * dt
        else:
            # Mid-air controls: stop horizontal movement if no key is pressed
            if not keys[K_LEFT] and not keys[K_RIGHT]:
                if player.velocity.x < 0:
                    player.velocity.x = -1
                elif player.velocity.x > 0:
                    player.velocity.x = 1
            if keys[K_LEFT]:
                player.velocity.x -= ACCELERATION * 0.5 * dt
            elif keys[K_RIGHT]:
                player.velocity.x += ACCELERATION * 0.5 * dt
        # UPDATE PLAYER
        just_landed = player.update(platforms, dt)
        
        # Check Combo
        if just_landed:
            jumped_floors = player.multi_jump  # current_platform.height - past_platform.height
            if jumped_floors >= 2:
                # START or CONTINUE the combo
                if state.combo == 0:
                    state.combo = jumped_floors
                    state.combo_start_time = current_time
                else:
                    state.combo += jumped_floors
                    state.combo_start_time = current_time

            elif jumped_floors < 2:
                if state.combo > 0:
                    state.score += int(state.combo ** 1.5)
                    state.combo = 0
                    
        if state.combo > 0:
            if (current_time - state.combo_start_time) >= COMBO_TIMEOUT:
                state.score += int(state.combo ** 1.5)
                state.combo = 0
                state.combo_floors = 0

        # DARK MODE LOGIC
        if just_landed:
            if not state.dark_mode and random.random() < DARK_MODE_CHANCE:
                state.dark_mode = True
                state.dark_mode_start_time = current_time
        
        
        # Turn off dark mode after 10 seconds
        if state.dark_mode and current_time - state.dark_mode_start_time > DARK_MODE_DURATION:
            state.dark_mode = False

        # CAMERA LOGIC
        # 1) Move camera up if player is near top
        desired_offset = player.rect.top - CAMERA_THRESHOLD
        if desired_offset < camera_offset:
            camera_offset = desired_offset

        # 2) After floor >= 5, do forced upward scrolling
        current_floor = player.current_platform.height
        if current_floor >= 5:
            forced_speed = state.base_speed + (state.speed_level * 0.5)
            camera_offset -= forced_speed * dt
            

        # SPAWN PLATFORMS ABOVE
        highest_p = min(platforms, key=lambda p: p.rect.y)
        while highest_p.rect.y > player.rect.y - SCREEN_HEIGHT:
            newp = Platform(previous_platform=highest_p, width = int(BASE_PLATFORM_WIDTH * state.platform_reduction_ratio), height = highest_p.height + 1)
            platforms.append(newp)
            highest_p = newp

        # UPDATE PLATFORMS (Remove platforms that are below screen)
        updated_list = []
        for p in platforms:
            #p.update(dt)
            # keep if not too far below
            if p.rect.top < camera_offset + SCREEN_HEIGHT + 100:
                updated_list.append(p)
        platforms = updated_list

        # SCORING
        if player.get_max_floor() > top_floor:
            diff = player.get_max_floor() - top_floor
            state.score += 10 * diff
            top_floor = player.get_max_floor()
            state.total_floors = top_floor

        # Speed Increase every Xs and platform size decrease
        if current_floor >= 5 and state.speed_level < MAX_SPEED_LEVEL:
            if (current_time - state.last_speed_increase) > DIFICULTY_INCREASE_TIME * 1000:
                state.speed_level += 1
                state.last_speed_increase = current_time
                if BASE_PLATFORM_WIDTH * (state.platform_reduction_ratio) > MIN_PLATFORM_WIDTH:
                    state.platform_reduction_ratio *= PLATFORM_REDUCTION_COEF

        # Game Over if below screen
        if player.rect.bottom - camera_offset > SCREEN_HEIGHT + 10:
            running = False

        # RENDER
        # Render Platforms
        for plat in platforms:
            plat.render(screen, camera_offset, player = player, light_radius = state.light_radius, dark_mode = state.dark_mode)
        player_pos = (player.rect.centerx, player.rect.centery - camera_offset)    
        if state.dark_mode:
            state.light_radius = calculate_light_radius(100, state.combo)
            light_mask = create_light_mask(player_pos, state.light_radius)
            screen.blit(light_mask, (0, 0))

        # RENDER PLAYER        
        player.render(screen, camera_offset)
        
        # HUD
        font_color = (255, 255, 255)
        # Render background and text
        screen.blit(font.render(f"Score: {state.score}", True, font_color), (10, SCREEN_HEIGHT - 25))
        screen.blit(font.render(f"Combo: {state.combo}", True, font_color), (10, 10))
        screen.blit(font.render(f"Dificulty: {state.speed_level}", True, (200, 200, 200)), (10, 50))

        pygame.display.flip()

    # Game over
    #screen.fill((0, 0, 0, 100))
    over_txt = font.render("Game Over!", True, (255, 255, 255))
    final_score = font.render(f"Final Score: {state.score}", True, (255, 255, 255))
    top_floor = font.render(f"Highest Floor: {player.get_max_floor()}", True, (255, 255, 255))
    # Get text surface dimensions
    over_txt_rect = over_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    final_score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
    top_floor_rect = top_floor.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

    # Blit the text surfaces
    screen.blit(over_txt, over_txt_rect.topleft)
    screen.blit(final_score, final_score_rect.topleft)
    screen.blit(top_floor, top_floor_rect.topleft)
    pygame.display.flip()
    waiting_for_key = True
    while waiting_for_key:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting_for_key = False  # Exit if the window is closed
            if event.type == pygame.KEYDOWN:
                waiting_for_key = False  # Exit if any key is pressed


if __name__ == "__main__":
    main()
