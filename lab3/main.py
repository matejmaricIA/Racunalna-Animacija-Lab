import pygame
import sys
import random
from pygame.locals import *
import json
from dynamic_background import DynamicBackground, BackgroundShape
from gamestate import GameState
from platform import Platform
from player import Player

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
        
        background.update(player.rect.y, SCREEN_HEIGHT, scroll_distance, camera_offset)
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
