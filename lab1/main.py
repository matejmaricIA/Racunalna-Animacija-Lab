import numpy as np
import pyglet
from pyglet.gl import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

cp_set = None
mesh_props = {"points": None, "faces": None}
ref_axis = None
total_segments = 0
sample_id = 0
seg_id = 0

param_range = np.linspace(0, 1, 20)
b_spline = np.array([
    [-1.,  3., -3.,  1.],
    [ 3., -6.,  3.,  0.],
    [-3.,  0.,  3.,  0.],
    [ 1.,  4.,  1.,  0.]
]) / 6.

cam_data = {"eye": [0., 0., 0.],
            "center": [0., 0., 0.],
            "up_dir": [0., 0., 1.]}

SCREEN_W, SCREEN_H = 1500, 800
cfg = pyglet.gl.Config(double_buffer=True, depth_size=24)
app_window = pyglet.window.Window(SCREEN_W, SCREEN_H, config=cfg)

def import_spline(path):
    global cp_set, total_segments, ref_axis
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line_str in f:
            line_str = line_str.strip()
            if not line_str or line_str[0] in ['#', 'g']:
                continue
            parts = line_str.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                if cp_set is None:
                    cp_set = np.array([[x, y, z]])
                else:
                    cp_set = np.vstack((cp_set, [x, y, z]))
    mx = np.max(cp_set, axis=0)
    mn = np.min(cp_set, axis=0)
    scale_val = np.max(mx - mn)
    cp_set /= scale_val
    total_segments = len(cp_set) - 3
    if total_segments > 0:
        v = cp_set[1] / np.linalg.norm(cp_set[1])
        ref_axis = np.reshape(v, (1, 3))

def import_mesh(path):
    global mesh_props
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line_str in f:
            line_str = line_str.strip()
            if not line_str or line_str[0] in ['#', 'g']:
                continue
            parts = line_str.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                if mesh_props["points"] is None:
                    mesh_props["points"] = np.array([[x, y, z]])
                else:
                    mesh_props["points"] = np.vstack((mesh_props["points"], [x, y, z]))
            elif parts[0] == 'f':
                i1, i2, i3 = map(int, parts[1:4])
                if mesh_props["faces"] is None:
                    mesh_props["faces"] = np.array([[i1, i2, i3]])
                else:
                    mesh_props["faces"] = np.vstack((mesh_props["faces"], [i1, i2, i3]))

def tick_animation(*_):
    global sample_id, seg_id
    sample_id += 1
    if sample_id >= len(param_range):
        sample_id = 0
        seg_id += 1
        if seg_id >= total_segments:
            seg_id = 0

def eval_point(t, c):
    p_mat = np.array([[t**3, t**2, t, 1]])
    return p_mat @ b_spline @ c

def eval_tangent(t, c):
    p_mat = np.array([[3*t**2, 2*t, 1, 0]])
    return p_mat @ b_spline @ c

def segment_coords(c):
    arr = None
    for v in param_range:
        pt = eval_point(v, c)
        if arr is None:
            arr = pt
        else:
            arr = np.vstack((arr, pt))
    return arr

def segment_tangents(c):
    arr = None
    for v in param_range:
        tg = eval_tangent(v, c)
        if arr is None:
            arr = tg
        else:
            arr = np.vstack((arr, tg))
    return arr

def get_spline_pos():
    seg_ctrl = cp_set[seg_id : seg_id + 4]
    return eval_point(param_range[sample_id], seg_ctrl)[0]

def vec_angle(a, b):
    dot_v = np.dot(a, b)
    mag = np.linalg.norm(a) * np.linalg.norm(b)
    return np.degrees(np.arccos(dot_v / mag))

def calc_rot_axis(b):
    return np.cross(ref_axis[0], b[0])

def setup_cam():
    global cam_data
    center_vals = np.mean(cp_set, axis=0)
    eye_vals = center_vals + np.array([2., 2., 5.])
    cam_data["eye"] = eye_vals.tolist()
    cam_data["center"] = center_vals.tolist()
    cam_data["up_dir"] = [0., 0., 1.]

def draw_spline():
    glPointSize(5)
    glColor3f(0.9, 0.2, 0.4)
    glBegin(GL_POINTS)
    for x in cp_set:
        glVertex3f(x[0], x[1], x[2])
    glEnd()
    glLoadIdentity()
    glPointSize(1)
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_LINE_STRIP)
    for i in range(total_segments):
        sub = cp_set[i : i + 4]
        pts = segment_coords(sub)
        tng = segment_tangents(sub) * 0.5
        for (p, t) in zip(pts, tng):
            glVertex3f(p[0], p[1], p[2])
            glVertex3f(p[0] + t[0], p[1] + t[1], p[2] + t[2])
    glEnd()

def draw_entity(rot=None):
    glPointSize(1)
    glColor3f(0.2, 0.8, 0.3)
    glScalef(0.12, 0.12, 0.12)
    glBegin(GL_TRIANGLES)
    for fc in mesh_props["faces"]:
        for idx in fc:
            v = mesh_props["points"][idx - 1]
            if rot is not None:
                v = np.dot(np.array([v]), rot)[0]
            glVertex3f(v[0], v[1], v[2])
    glEnd()

@app_window.event
def on_draw():
    if not callable(glMatrixMode):
        return
    glEnable(GL_DEPTH_TEST)
    glClearColor(0., 0., 0.1, 1.)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(10.0, float(SCREEN_W)/float(SCREEN_H), 0.1, 100.)
    gluLookAt(cam_data["eye"][0], cam_data["eye"][1], cam_data["eye"][2],
              cam_data["center"][0], cam_data["center"][1], cam_data["center"][2],
              cam_data["up_dir"][0], cam_data["up_dir"][1], cam_data["up_dir"][2])
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    draw_spline()
    pos = get_spline_pos()
    glTranslatef(*pos)
    subset = cp_set[seg_id : seg_id + 4]
    tg = eval_tangent(param_range[sample_id], subset)
    tg = np.reshape(tg, (1, 3))
    ax = calc_rot_axis(tg)
    an = vec_angle(ref_axis[0], tg[0])
    glRotatef(an, *ax)
    draw_entity()

def run():
    pyglet.clock.schedule(tick_animation)
    pyglet.app.run()

if __name__ == "__main__":
    import_spline("assets/path.obj")
    import_mesh("assets/bird.obj")
    setup_cam()
    run()
