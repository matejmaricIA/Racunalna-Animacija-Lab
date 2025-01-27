import json
import os
import subprocess
import dearpygui.dearpygui as dpg
import sys

# Paths
SETTINGS_FILE = "settings.json"
GAME_SCRIPT = "main.py"

# Default settings
DEFAULT_SETTINGS_FILE = "default_settings.json"
# Track the game process
game_process = None

DEFAULT_SETTINGS = {
    "Physics": {
        "GRAVITY": 0.8999999761581421,
        "BASE_JUMP": -15,
        "VERTICAL_SPEED_JUMP_INCREASE": 0.20000000298023224,
        "FRICTION": 0.1499999761581421,
        "ACCELERATION": 0.30000001192092896
    },
    "Game World": {
        "SCREEN_WIDTH": 700,
        "SCREEN_HEIGHT": 800,
        "PLAYER_SIZE": 25,
        "PLATFORM_HEIGHT": 20,
        "CAMERA_THRESHOLD": 200,
        "PLATFORM_SPACING": 80,
        "BASE_PLATFORM_WIDTH": 200,
        "MIN_PLATFORM_WIDTH": 20,
        "MAX_SPEED_LEVEL": 15,
        "PLATFORM_SHAKE_DURATION": 1500,
        "DIFFICULTY_INCREASE_TIMER": 30,
        "PLATFORM_REDUCTION_COEF": 0.949999988079071,
        "COMBO_TIMEOUT": 3000,
        "DARK_MODE_CHANCE": 0.05000000074505806,
        "DARK_MODE_DURATION": 10000
    },
    "Colors": {
        "PLAYER_COLOR": [255, 0, 0],
        "PLATFORM_COLOR": [0, 0, 255],
        "GRADIENT_TOP_COLOR": [135, 206, 235],
        "GRADIENT_BOTTOM_COLOR": [25, 25, 112]
    }
}


def resource_path(relative_path):
    """ Get the absolute path to the resource, works for PyInstaller bundles. """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # PyInstaller's temp folder
    return os.path.join(os.path.abspath("."), relative_path)

def load_settings():
    # Load last settings first
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    
    # Fallback to `default_settings.json` or hardcoded defaults
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, "r") as f:
            return json.load(f)
    
    return DEFAULT_SETTINGS.copy()


# Save settings to file
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def save_callback():
    settings = {"Physics": {}, "Game World": {}, "Colors": {}}
    for category, category_dict in DEFAULT_SETTINGS.items():
        for key in category_dict:
            settings[category][key] = dpg.get_value(key)
    save_settings(settings)
    print("Settings saved!")
    
def save_as_default_callback():
    settings = {"Physics": {}, "Game World": {}, "Colors": {}}
    for category, category_dict in DEFAULT_SETTINGS.items():
        for key in category_dict:
            settings[category][key] = dpg.get_value(key)
    
    # Save to the default settings file
    with open(DEFAULT_SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    print("Current settings saved as default!")


# Callback for "Return to Default" button
def return_to_default_callback():
    # Check if `default_settings.json` exists
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, "r") as f:
            default_settings = json.load(f)
    for category, category_dict in default_settings.items():
        for key, value in category_dict.items():
            dpg.set_value(key, value)
    print("Returned to default settings (not saved yet).")


# Callback for "Play" button
def play_callback():
    global game_process
    save_callback()  # Save settings first
    if game_process is None:
        try:
            # Launch the game
            game_process = subprocess.Popen(["python", GAME_SCRIPT])
            print("Game launched!")
        except FileNotFoundError:
            print(f"Could not find {GAME_SCRIPT}. Make sure it exists in the same directory.")
    else:
        print("Game is already running!")


# Callback for "Stop Game" button
def stop_game_callback():
    global game_process
    if game_process is not None:
        game_process.terminate()
        game_process = None
        print("Game process terminated.")
    else:
        print("No game process is running.")


# Create the configuration UI
def create_config_ui():
    settings = load_settings()

    with dpg.window(label="Game Configuration", width=600, height=750):
        dpg.add_text("Adjust the game settings below:")
        dpg.add_separator()
        
        # Physics settings
        with dpg.collapsing_header(label="Physics", default_open=False):
            for key, value in settings["Physics"].items():
                if isinstance(settings["Physics"][key], int):
                    dpg.add_input_int(tag=key, label=key, default_value=settings["Physics"][key], width=200)
                elif isinstance(settings["Physics"][key], float):
                    dpg.add_input_float(tag=key, label=key, default_value=settings["Physics"][key], width=200)
                    
        # Game World settings
        with dpg.collapsing_header(label="Game World", default_open=False):
            for key, value in settings["Game World"].items():
                if isinstance(settings["Game World"][key], int):
                    dpg.add_input_int(tag=key, label=key, default_value=settings["Game World"][key], width=200)
                elif isinstance(settings["Game World"][key], float):
                    dpg.add_input_float(tag=key, label=key, default_value=settings["Game World"][key], width=200)
                    
         # Color settings
        with dpg.collapsing_header(label="Colors", default_open=False):
            for key, value in settings["Colors"].items():
                dpg.add_color_edit(tag=key, label=key, default_value=value, width=300)  # RGB selector
        
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(label="Save", callback=save_callback, width=100)
            dpg.add_button(label="Save as Default", callback=save_as_default_callback, width=150)
            dpg.add_button(label="Return to Default", callback=return_to_default_callback, width=150)
            dpg.add_button(label="Play", callback=play_callback, width=100)

        dpg.add_button(label="Stop Game", callback=stop_game_callback, width=100)


# Main function
def main():
    dpg.create_context()
    dpg.create_viewport(title="Game Configuration", width=600, height=700, resizable=False)
    create_config_ui()
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
