import numpy as np
import pyglet
from pyglet.gl import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


current_segment_t = 0 # Trenutni param korak na segmentu krivulje
seg_id = 0 # Trenutni segment krivulje


SCREEN_W, SCREEN_H = 1500, 800
cfg = pyglet.gl.Config(double_buffer=True, depth_size=24)
app_window = pyglet.window.Window(SCREEN_W, SCREEN_H, config=cfg)

def import_spline(path, control_points, total_segments, ref_axis):
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line[0] in ['#', 'g']:
                continue
            parts = line.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                if control_points is None:
                    control_points = np.array([[x, y, z]]) # Ako je skup kontrolni točaka prazan, inicijaliziraj ga
                else:
                    control_points = np.vstack((control_points, [x, y, z])) # dodaj novi red u matricu

    mx = np.max(control_points, axis=0)
    mn = np.min(control_points, axis=0)
    scale_val = np.max(mx - mn)
    control_points /= scale_val # Kontrolne točke se skaliraju kako bi stale na ekran
    total_segments = len(control_points) - 3  # Svaki segment je definiran sa 4 kontrolne točke, a s n točaka određeno je n - 3 segmenata krivulje
    if total_segments > 0:
        v = control_points[1] / np.linalg.norm(control_points[1]) # Incijalni vektor orijentacije koji se normalizira da bi mu duljina bila 1
        ref_axis = np.reshape(v, (1, 3))
    return control_points, total_segments, ref_axis
        
# Učitava model iz .obj datoteke koji će se kretati po b-splajn krivulji
def load_model(path, object_data):
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # Učitavanje vrhova
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4]) # Dobivanje koordinata vrha
                if object_data["points"] is None:
                    object_data["points"] = np.array([[x, y, z]]) # ako je object_data prazan, incijalziraj ga
                else:
                    object_data["points"] = np.vstack((object_data["points"], [x, y, z]))
            # Učitavanje ploha
            elif parts[0] == 'f':
                i1, i2, i3 = map(int, parts[1:4])
                if object_data["faces"] is None:
                    object_data["faces"] = np.array([[i1, i2, i3]])
                else:
                    object_data["faces"] = np.vstack((object_data["faces"], [i1, i2, i3]))
       
    # Normaliziraj veličinu modela
    max_val = np.max(object_data["points"], axis=0)
    min_val = np.min(object_data["points"], axis=0)
    scale_factor = np.max(max_val - min_val)
    object_data["points"] /= scale_factor  # Scale model to fit within [-1,1] range

    return object_data

def tick_animation(*_):
    global current_segment_t, seg_id
    current_segment_t += 1
    # Ako smo prošli sve korake na trenutnom segmentu, prelazimo na sljedeći segment seg_id
    if current_segment_t >= len(param_range):
        current_segment_t = 0
        seg_id += 1
        if seg_id >= total_segments:
            seg_id = 0

def calc_point(t_i, seg_control_points):
    t_mat = np.array([[t_i**3, t_i**2, t_i, 1]])
    return t_mat @ b_spline @ seg_control_points # Izlaz: koordinate točke p_i(t) na B-splajn krivulji

def calc_tangent(t_i, seg_control_points):
    t_mat = np.array([[3*t_i**2, 2*t_i, 1, 0]]) # Derivacija
    return t_mat @ b_spline @ seg_control_points # Vektor tangente u točki na krivulji

def calc_second_derivative(t_i, seg_control_points):
    t_mat = np.array([[6*t_i, 2, 0, 0]])  # Druga derivacija
    return t_mat @ b_spline @ seg_control_points

# Izračun svih točaka na segmentu
def segment_coords(seg_control_points):
    segment = None
    for t in param_range: # Prolazimo kroz sve vrijednosti t (0 do 1)
        pt = calc_point(t, seg_control_points) # Računamo točku na krivulji
        if segment is None:
            segment = pt
        else:
            segment = np.vstack((segment, pt))
    return segment # Lista točaka segmenta na krivulji

# Izračunavanje svih tangenti na segmentu
def segment_tangents(seg_control_points):
    tangs = None
    for t in param_range:
        tg = calc_tangent(t, seg_control_points)
        if tangs is None:
            tangs = tg
        else:
            tangs = np.vstack((tangs, tg))
    return tangs

# Dohvaćanje trenutne pozicije objekta na putanji
def get_spline_pos():
    seg_ctrl = control_points[seg_id : seg_id + 4] # 4 kontrolne točke tren segmenta
    return calc_point(param_range[current_segment_t], seg_ctrl)[0] # Računa se pozicija na krivulji

# Računanje kuta između dva vektora (koliko se objekt treba rotirati od svog originalnog referentnog smjera)
def vec_angle(s, e):
    dot_v = np.dot(s, e)
    mag = np.linalg.norm(s) * np.linalg.norm(e) # Umnožak duljina vektora
    return np.degrees(np.arccos(dot_v / mag)) # Izračun kuta i konverzija u stupnjeve

# Iračun osi rotacije (izračun osi rotacije između referentne osi i trenutne tangente)
def calc_rot_axis(e):
    return np.cross(ref_axis[0], e[0]) # Vektorski umnožak referentne osi i tangente

# Postavljanje kamere
def setup_cam(cam_data):
    center_vals = np.mean(control_points, axis=0) # Prosječna točka kontrolnih točaka
    pos_vals = center_vals + np.array([1., 1., 4.])
    cam_data["pos"] = pos_vals.tolist()
    cam_data["center"] = center_vals.tolist()
    cam_data["up_dir"] = [0., 0., 1.] # Os "prema gore" postavljena na Z-os

# Iscrtvanje krivulje i tangenti
def draw_spline():
    glPointSize(5)
    glColor3f(0.9, 0.2, 0.4) # Boja kontrolnih točaka
    glBegin(GL_POINTS)
    for x in control_points:
        glVertex3f(x[0], x[1], x[2])
    glEnd()
    glLoadIdentity()
    glPointSize(1)
    glColor3f(0.9, 0.9, 0.9) # Boja krivulje
    glBegin(GL_LINE_STRIP)
    for i in range(total_segments):
        sub = control_points[i : i + 4] # Dohvati 4 kontrolne točke za trenutni segment
        pts = segment_coords(sub) # Izračunaj sve točke na segmentu
        tng = segment_tangents(sub) # Izračunaj tangente
        for (p, t) in zip(pts, tng):
            glVertex3f(p[0], p[1], p[2])
            glVertex3f(p[0] + t[0], p[1] + t[1], p[2] + t[2])
    glEnd()

# Iscrtavanje objekta koji se kreće duž putanje
def draw_entity(rot=None):
    glPointSize(1)
    glColor3f(0.2, 0.8, 0.3)
    glScalef(0.2, 0.2, 0.2)
    #glScalef(0.01, 0.01, 0.01) # Skalira model
    glBegin(GL_TRIANGLES)
    for fc in object_data["faces"]: # Iterira kroz sve plohe modela
        for idx in fc:
            v = object_data["points"][idx - 1] # Dohvati koordinate vrha
            if rot is not None:
                v = np.dot(np.array([v]), rot)[0] # Primjeni rotaciju ako postoji
            glVertex3f(v[0], v[1], v[2])
    glEnd()
    
def calculate_dcm():
    current_params = param_range[current_segment_t], control_points[seg_id:seg_id + 4]
    
    w = calc_tangent(*current_params)  # Prva derivacija (tangenta)
    #w /= np.linalg.norm(w)  # Normaliziraj

    dt_dt = calc_second_derivative(*current_params)  # Druga derivacija
    u = np.cross(w, dt_dt)  # Izračunaj normalu
    
    #u /= np.linalg.norm(u)  # Normaliziraj normalu
    v = np.cross(w, u)  # Izračunaj binormalu
    #v /= np.linalg.norm(v)  # Normaliziraj binormalu

    rotation_matrix = np.vstack((w, u, v)).T  
    #print(w, u, v)

    return rotation_matrix


@app_window.event
def on_draw():
    if not callable(glMatrixMode):
        return
    glEnable(GL_DEPTH_TEST)
    glClearColor(0., 0., 0.1, 1.)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION) # definira kako se 3d scena projicira na 2d ekran
    glLoadIdentity()
    gluPerspective(10.0, float(SCREEN_W)/float(SCREEN_H), 0.1, 100.)
    gluLookAt(cam_data["pos"][0], cam_data["pos"][1], cam_data["pos"][2],
              cam_data["center"][0], cam_data["center"][1], cam_data["center"][2],
              cam_data["up_dir"][0], cam_data["up_dir"][1], cam_data["up_dir"][2])
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    draw_spline()
    pos = get_spline_pos() # Računa trenutnu poziciju na krivulji
    glTranslatef(pos[0], pos[1], pos[2]) # Pomiče objekt na tu poziciju
    subset = control_points[seg_id : seg_id + 4]
    
    tg = calc_tangent(param_range[current_segment_t], subset) # Tangenta na trenutnoj poziciji
    tg = np.reshape(tg, (1, 3))
    rotation_axis = calc_rot_axis(tg) # Pronalazi os rotacije između trenutnog smjera i referentnog
    angle = vec_angle(ref_axis[0], tg[0]) # Kut rotacije
    glRotatef(angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])
    
    draw_entity()
    
    #glScalef(20, 20,  20)
    #dcm = calculate_dcm()
    #draw_entity(dcm)

def run():
    pyglet.clock.schedule(tick_animation)
    pyglet.app.run()

if __name__ == "__main__":
    control_points = None # Skup kontrolnih točaka za krivulju
    object_data = {"points": None, "faces": None} # points i faces (koordinate vrhova i plohe (kako su vrhovi povezani))
    ref_axis = None # Referentna os za inicijalnu orjentaciju
    total_segments = 0 # Ukupni broj segmenata


    param_range = np.linspace(0, 1, 20)
    b_spline = np.array([
        [-1.,  3., -3.,  1.],
        [ 3., -6.,  3.,  0.],
        [-3.,  0.,  3.,  0.],
        [ 1.,  4.,  1.,  0.]
    ]) / 6.

    cam_data = {"pos": [0., 0., 0.],
                "center": [0., 0., 0.],
                "up_dir": [0., 0., 0.]}
    
    control_points, total_segments, ref_axis = import_spline("assets/path.obj", control_points, 
                                                             total_segments, ref_axis)
    object_data = load_model("assets/teddy.obj", object_data)
    setup_cam(cam_data)
    run()
