"""
Camera presets for Display-Puck GC9A01 renderings (Fusion Python API).

The model is built in print coordinates (front face on Z=0). Instead of moving
occurrences, the camera up-vector is tilted, so the puck appears standing on the desk.

Usage (Fusion MCP / script): exec this file, then call
    apply_view("hero")          # or: "front", "side", "rear", "exploded", "lid"
"""

import math

import adsk.core
import adsk.fusion

TILT_DEG = 15.0
CAMERA_DISTANCE_CM = 30.0
TARGET_MM = (0.0, -4.0, 17.0)       # puck centre (local coords)
EXPLODE_COVER_MM = 62.0             # lid (+ ESP) offset for the exploded view (+Z)
EXPLODE_RING_MM = 36.0              # clamp ring offset for the exploded view (+Z)
COMP_BODY = "Gehaeuse"
COMP_COVER = "Deckel"
COMP_RING = "Klemmring"
COMP_REF = "Referenz Display (nicht drucken)"
COMP_REF_ESP = "Referenz ESP32 (nicht drucken)"

_T = math.radians(TILT_DEG)
UP = (0.0, math.cos(_T), -math.sin(_T))          # world up in local coords
FWD = (0.0, -math.sin(_T), -math.cos(_T))        # towards the viewer (horizontal)
SIDE = (1.0, 0.0, 0.0)

# view name -> (forward, side, up) weights of the eye direction, visibility map
VIEWS = {
    "hero":     ((0.80, -0.55, 0.38), {COMP_REF: True, COMP_REF_ESP: True}),
    "front":    ((1.00, 0.00, 0.12), {COMP_REF: True, COMP_REF_ESP: True}),
    "side":     ((0.00, -1.00, 0.05), {COMP_REF: False, COMP_REF_ESP: False}),
    "rear":     ((-0.80, -0.55, 0.35), {COMP_REF: False, COMP_REF_ESP: False}),
    "exploded": ((-0.45, -0.85, 0.40), {COMP_REF: True, COMP_REF_ESP: True}),
    "lid":      ((1.00, -0.45, 0.35), {COMP_BODY: False, COMP_RING: False, COMP_REF: False}),
}


def _vec(weights):
    f, s, u = weights
    v = [f * FWD[i] + s * SIDE[i] + u * UP[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def _occ(root, name):
    for occ in root.occurrences:
        if occ.component.name == name:
            return occ
    return None


def _offset(occ, dz_mm):
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(0, 0, dz_mm / 10.0)
    occ.transform2 = m


def apply_view(name: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    weights, vis = VIEWS[name]

    for comp_name in (COMP_BODY, COMP_COVER, COMP_RING, COMP_REF, COMP_REF_ESP):
        occ = _occ(root, comp_name)
        if occ:
            occ.isLightBulbOn = vis.get(comp_name, True)
    exploded = name == "exploded"
    for comp_name, dz in ((COMP_COVER, EXPLODE_COVER_MM), (COMP_REF_ESP, EXPLODE_COVER_MM),
                          (COMP_RING, EXPLODE_RING_MM)):
        occ = _occ(root, comp_name)
        if occ:
            _offset(occ, dz if exploded else 0.0)

    d = _vec(weights)
    tx, ty, tz = (c / 10.0 for c in TARGET_MM)
    cam = app.activeViewport.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    cam.target = adsk.core.Point3D.create(tx, ty, tz)
    cam.eye = adsk.core.Point3D.create(tx + d[0] * CAMERA_DISTANCE_CM,
                                       ty + d[1] * CAMERA_DISTANCE_CM,
                                       tz + d[2] * CAMERA_DISTANCE_CM)
    cam.upVector = adsk.core.Vector3D.create(*UP)
    app.activeViewport.camera = cam
    app.activeViewport.fit()
    app.activeViewport.refresh()
    return f"view {name} applied"


def run(context):
    pass
