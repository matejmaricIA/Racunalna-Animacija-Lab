import json
import os
import subprocess
import dearpygui.dearpygui as dpg
import sys

def load_default():
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, "r") as f:
            return json.load(f)

# Paths
SETTINGS_FILE = "settings/settings.json"
GAME_SCRIPT = "main.py"

# Default settings
DEFAULT_SETTINGS_FILE = "settings/default_settings.json"
# Track the game process
game_process = None
DEFAULT_SETTINGS = load_default()

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

    with dpg.window(label="Game Configuration", width=600, height=750, no_scrollbar = False):
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
    dpg.create_viewport(title="Game Configuration", width=500, height=700, resizable=True)
    create_config_ui()
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
