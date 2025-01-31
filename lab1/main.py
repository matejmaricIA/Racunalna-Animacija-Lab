import numpy as np
import pyglet
from pyglet.gl import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

cpSet = None
meshProps = {"points": None, "faces": None}
refAxis = None
totalSegments = 0
sampleId = 0
segId = 0

paramRange = np.linspace(0, 1, 20)
Bspline = np.array([
    [-1.,  3., -3.,  1.],
    [ 3., -6.,  3.,  0.],
    [-3.,  0.,  3.,  0.],
    [ 1.,  4.,  1.,  0.]
]) / 6.

camData = {"eye": [0., 0., 0.],
           "center": [0., 0., 0.],
           "up_dir": [0., 0., 1.]}

W, H = 1500, 800
cfg = pyglet.gl.Config(double_buffer=True, depth_size=24)
window = pyglet.window.Window(W, H, config=cfg)

def importSpline(path):
    global cpSet, totalSegments, refAxis
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line in f:
            s = line.strip()
            if not s or s[0] in ['#', 'g']:
                continue
            parts = s.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                if cpSet is None:
                    cpSet = np.array([[x, y, z]])
                else:
                    cpSet = np.vstack((cpSet, [x, y, z]))
    mx = np.max(cpSet, axis=0)
    mn = np.min(cpSet, axis=0)
    scale = np.max(mx - mn)
    cpSet /= scale
    totalSegments = len(cpSet) - 3
    if totalSegments > 0:
        v = cpSet[1] / np.linalg.norm(cpSet[1])
        refAxis = np.reshape(v, (1, 3))

def importMesh(path):
    global meshProps
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj is allowed.")
    with open(path, 'r') as f:
        for line in f:
            s = line.strip()
            if not s or s[0] in ['#', 'g']:
                continue
            parts = s.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                if meshProps["points"] is None:
                    meshProps["points"] = np.array([[x, y, z]])
                else:
                    meshProps["points"] = np.vstack((meshProps["points"], [x, y, z]))
            elif parts[0] == 'f':
                i1, i2, i3 = map(int, parts[1:4])
                if meshProps["faces"] is None:
                    meshProps["faces"] = np.array([[i1, i2, i3]])
                else:
                    meshProps["faces"] = np.vstack((meshProps["faces"], [i1, i2, i3]))

def tickAnimation(*_):
    global sampleId, segId
    sampleId += 1
    if sampleId >= len(paramRange):
        sampleId = 0
        segId += 1
        if segId >= totalSegments:
            segId = 0

def evalPoint(t, c):
    P = np.array([[t**3, t**2, t, 1]])
    return P @ Bspline @ c

def evalTangent(t, c):
    P = np.array([[3*t**2, 2*t, 1, 0]])
    return P @ Bspline @ c

def segmentCoords(c):
    out = None
    for v in paramRange:
        rr = evalPoint(v, c)
        if out is None:
            out = rr
        else:
            out = np.vstack((out, rr))
    return out

def segmentTangents(c):
    out = None
    for v in paramRange:
        rr = evalTangent(v, c)
        if out is None:
            out = rr
        else:
            out = np.vstack((out, rr))
    return out

def getSplinePos():
    c = cpSet[segId : segId + 4]
    return evalPoint(paramRange[sampleId], c)[0]

def vecAngle(a, b):
    dotv = np.dot(a, b)
    nm = np.linalg.norm(a)*np.linalg.norm(b)
    return np.degrees(np.arccos(dotv / nm))

def calcRotAxis(b):
    return np.cross(refAxis[0], b[0])

def setupCam():
    global camData
    c = np.mean(cpSet, axis=0)
    e = c + np.array([2., 2., 5.])
    camData["eye"] = e.tolist()
    camData["center"] = c.tolist()
    camData["up_dir"] = [0., 0., 1.]

def drawSpline():
    glPointSize(5)
    glColor3f(0.9, 0.2, 0.4)
    glBegin(GL_POINTS)
    for x in cpSet:
        glVertex3f(x[0], x[1], x[2])
    glEnd()
    glLoadIdentity()
    glPointSize(1)
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_LINE_STRIP)
    for i in range(totalSegments):
        sub = cpSet[i : i + 4]
        pts = segmentCoords(sub)
        tng = segmentTangents(sub) * 0.5
        for (p, t) in zip(pts, tng):
            glVertex3f(p[0], p[1], p[2])
            glVertex3f(p[0]+t[0], p[1]+t[1], p[2]+t[2])
    glEnd()

def drawEntity(rot=None):
    glPointSize(1)
    glColor3f(0.2, 0.8, 0.3)
    glScalef(0.12, 0.12, 0.12)
    glBegin(GL_TRIANGLES)
    for fc in meshProps["faces"]:
        for idx in fc:
            v = meshProps["points"][idx - 1]
            if rot is not None:
                v = np.dot(np.array([v]), rot)[0]
            glVertex3f(v[0], v[1], v[2])
    glEnd()

@window.event
def on_draw():
    if not callable(glMatrixMode):
        return
    glEnable(GL_DEPTH_TEST)
    glClearColor(0., 0., 0.1, 1.)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(10.0, float(W)/float(H), 0.1, 100.)
    gluLookAt(camData["eye"][0], camData["eye"][1], camData["eye"][2],
              camData["center"][0], camData["center"][1], camData["center"][2],
              camData["up_dir"][0], camData["up_dir"][1], camData["up_dir"][2])
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    drawSpline()
    pos = getSplinePos()
    glTranslatef(*pos)
    subset = cpSet[segId : segId + 4]
    tg = evalTangent(paramRange[sampleId], subset)
    tg = np.reshape(tg, (1, 3))
    ax = calcRotAxis(tg)
    an = vecAngle(refAxis[0], tg[0])
    glRotatef(an, *ax)
    drawEntity()

def run():
    pyglet.clock.schedule(tickAnimation)
    pyglet.app.run()

if __name__ == "__main__":
    importSpline("assets/path.obj")
    importMesh("assets/bird.obj")
    setupCam()
    run()
