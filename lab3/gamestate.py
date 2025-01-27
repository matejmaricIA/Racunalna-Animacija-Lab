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
        


