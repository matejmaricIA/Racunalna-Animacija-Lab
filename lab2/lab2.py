import pyglet
import random
import math

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 700
window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, 'Simulacija Snijega')

# Parametri simulacije
NEW_FLAKES_PER_FRAME = 2
WIND_STRENGTH = 3000   
GRAVITY = -80    
WIND_RADIUS = 50
ROTATION_SPEED = 30
MAX_SNOWFLAKES = 2000

# Učitavanje slike pahulje
snowflake_img = pyglet.image.load('snow.bmp')
snowflake_img.anchor_x = snowflake_img.width // 2
snowflake_img.anchor_y = snowflake_img.height // 2

#batch = pyglet.graphics.Batch()

far_batch = pyglet.graphics.Batch()
middle_batch = pyglet.graphics.Batch()
close_batch = pyglet.graphics.Batch()

class Snowflake:

    def __init__(self, x, y):
        self.depth_factor = random.uniform(0.01, 1.0)
        if self.depth_factor < 0.4:
            self.sprite = pyglet.sprite.Sprite(snowflake_img, x=x, y=y, batch=far_batch)
            self.rotation_speed = random.choice([-(ROTATION_SPEED - 10), ROTATION_SPEED - 10])
        elif self.depth_factor < 0.7:
            self.sprite = pyglet.sprite.Sprite(snowflake_img, x=x, y=y, batch=middle_batch)
            self.rotation_speed = random.choice([-(ROTATION_SPEED - 5), ROTATION_SPEED - 5])
        else:
            self.sprite = pyglet.sprite.Sprite(snowflake_img, x=x, y=y, batch=close_batch)
            self.rotation_speed = random.choice([-(ROTATION_SPEED), ROTATION_SPEED])    
        self.vx = 0

        self.vy = 0
        self.sprite.scale = 0.05 + 0.1 * self.depth_factor
        self.sprite.opacity = int(255 * self.depth_factor)

snowflakes = []

mouse_pressed = False
mouse_x = 0
mouse_y = 0

def create_snowflakes():
    for _ in range(NEW_FLAKES_PER_FRAME):
        x = random.uniform(0, WINDOW_WIDTH)
        y = WINDOW_HEIGHT + 30  # malo iznad vrha ekrana
        snowflakes.append(Snowflake(x, y))
    #print(len(snowflakes))

def update_snowflakes(dt):
    # Dodajemo nove pahulje
    if len(snowflakes) <= MAX_SNOWFLAKES:
        create_snowflakes()
    
    to_remove = []
    for flake in snowflakes:
        # Primijeni gravitaciju
        flake.vy += GRAVITY * dt * (flake.depth_factor * 1.2)
        flake.vx += random.uniform(-4, 4) * (flake.depth_factor * 1.2)
        
        if mouse_pressed:
            # Izračunaj vektor od točke miša do pahulje
            dx = flake.sprite.x - mouse_x
            dy = flake.sprite.y - mouse_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Što je pahulja bliže točki, to je jača sila
            if dist < WIND_RADIUS:  # radijus djelovanja vjetra

                if dist > 0:
                    ndx = dx / dist
                    ndy = dy / dist
                else:
                    ndx = 0
                    ndy = 0
                flake.vx += ndx * WIND_STRENGTH * dt * (flake.depth_factor * 1.2)
                flake.vy += ndy * WIND_STRENGTH * dt * (flake.depth_factor * 1.2)
                #print('depth factor: {}, vx: {}, vy: {}'.format(flake.depth_factor, flake.vx, flake.vy))

        # Ažuriraj poziciju pahulje
        flake.sprite.x += flake.vx * dt
        flake.sprite.y += flake.vy * dt
        flake.sprite.rotation += flake.rotation_speed * dt

        # Uklanjanje pahulja
        if flake.sprite.y < -50 or flake.sprite.x < -50 or flake.sprite.x > WINDOW_WIDTH + 50:
            to_remove.append(flake)

    for flake in to_remove:
        snowflakes.remove(flake)
        
@window.event
def on_mouse_press(x, y, button, modifiers):
    global mouse_pressed, mouse_x, mouse_y
    if button == pyglet.window.mouse.LEFT:
        mouse_pressed = True
        mouse_x = x
        mouse_y = y

@window.event
def on_mouse_release(x, y, button, modifiers):
    global mouse_pressed
    if button == pyglet.window.mouse.LEFT:
        mouse_pressed = False

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global mouse_x, mouse_y
    # Ako se drži lijevi klik i mičemo miš, ažuriraj poziciju
    if buttons & pyglet.window.mouse.LEFT:
        mouse_x = x
        mouse_y = y

@window.event
def on_draw():
    window.clear()
    far_batch.draw()
    middle_batch.draw()
    close_batch.draw()

def update(dt):
    update_snowflakes(dt)

if __name__ == '__main__':
    pyglet.clock.schedule_interval(update, 1/60.0)
    pyglet.app.run()
