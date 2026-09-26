"""
Print-plate layout for Display-Puck GC9A01 (run inside Fusion on the built document).

Puts all printable parts side by side in print orientation on Z=0:
  Gehaeuse   front face down (as modelled)
  Deckel     rotated 180° about X (outer face down)
  Klemmring  flat, next to the lid
Reference parts are hidden. Optionally exports the plate as 3MF and saves a new version.

apply_layout("print")      -> plate layout
apply_layout("assembled")  -> back to the assembled position
"""

import math
import os

import adsk.core
import adsk.fusion

# Project root = parent of this fusion/ folder. Fusion's script runner sets __file__;
# when exec'd through the MCP bridge the caller puts __file__ into the namespace.
PROJECT_DIR_FALLBACK = "/Users/jakob/Projekte/Display-Case-GC9A01/puck"
PROJECT_DIR = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
               if "__file__" in globals() else PROJECT_DIR_FALLBACK)
PLATE_3MF = os.path.join(PROJECT_DIR, "3MF", "PUCK-Druckplatte-Fusion.3mf")
PART_GAP_MM = 10.0          # spacing between parts on the plate
PLATE_SIZE_MM = 256.0       # Bambu A1 / P1S build plate
SAVE_NOTE = "Druckplatten-Layout (alle Teile nebeneinander)"

COMP_BODY = "Gehaeuse"
COMP_COVER = "Deckel"
COMP_RING = "Klemmring"
REF_PREFIX = "Referenz"
PRINT_PARTS = (COMP_BODY, COMP_COVER, COMP_RING)


def _occ(root, name):
    for occ in root.occurrences:
        if occ.component.name == name:
            return occ
    raise RuntimeError(f"component '{name}' not found - run build_puck.py first")


def _native_bbox_mm(occ):
    """Bounding box of the component's body in component (unmoved) coordinates."""
    bb = occ.component.bRepBodies.item(0).boundingBox
    return ([v * 10.0 for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z)],
            [v * 10.0 for v in (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])


def _matrix(flip_x: bool, tx_mm: float, ty_mm: float, tz_mm: float):
    m = adsk.core.Matrix3D.create()
    if flip_x:
        m.setToRotation(math.pi, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
    t = m.translation
    m.translation = adsk.core.Vector3D.create(t.x + tx_mm / 10.0, t.y + ty_mm / 10.0, t.z + tz_mm / 10.0)
    return m


def _place(occ, flip_x: bool, x_left_mm: float):
    """Place a part with its left edge at x_left, centred on Y=0, resting on Z=0."""
    lo, hi = _native_bbox_mm(occ)
    if flip_x:  # (x, y, z) -> (x, -y, -z)
        lo, hi = [lo[0], -hi[1], -hi[2]], [hi[0], -lo[1], -lo[2]]
    tx = x_left_mm - lo[0]
    ty = -(lo[1] + hi[1]) / 2.0
    tz = -lo[2]
    occ.transform2 = _matrix(flip_x, tx, ty, tz)
    return x_left_mm + (hi[0] - lo[0])


def _world_bbox_mm(occ):
    bb = occ.bRepBodies.item(0).boundingBox  # proxy -> assembly coordinates
    return ([round(v * 10.0, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z)],
            [round(v * 10.0, 2) for v in (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])


def apply_layout(mode: str = "print", export: bool = True, save: bool = True):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    log = []

    for occ in root.occurrences:
        if occ.component.name.startswith(REF_PREFIX):
            occ.isLightBulbOn = mode != "print"
    occs = {name: _occ(root, name) for name in PRINT_PARTS}
    for occ in occs.values():
        occ.isLightBulbOn = True
        if occ.isGrounded:  # Fusion grounds the first component -> transform2 is ignored
            occ.isGrounded = False

    if mode == "print":
        # Gehaeuse stays at the origin: it is modelled in print orientation already, and a
        # position snapshot resets the first component anyway. Lid + ring go next to it.
        occs[COMP_BODY].transform2 = adsk.core.Matrix3D.create()
        _, body_hi = _native_bbox_mm(occs[COMP_BODY])
        body_lo, _ = _native_bbox_mm(occs[COMP_BODY])
        x = body_hi[0] + PART_GAP_MM
        x = _place(occs[COMP_COVER], True, x) + PART_GAP_MM
        x = _place(occs[COMP_RING], False, x)
        row = x - body_lo[0]
        if row > PLATE_SIZE_MM:
            raise RuntimeError(f"row {row:.1f} mm does not fit on a {PLATE_SIZE_MM:.0f} mm plate")
        log.append(f"plate row width {row:.1f} mm (plate {PLATE_SIZE_MM:.0f} mm)")
    elif mode == "assembled":
        for occ in occs.values():
            occ.transform2 = adsk.core.Matrix3D.create()
    else:
        raise ValueError(f"unknown mode {mode}")

    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType and design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    for name, occ in occs.items():
        lo, hi = _world_bbox_mm(occ)
        log.append(f"{name}: min {lo} max {hi}")

    if mode == "print" and export:
        em = design.exportManager
        opts = em.createC3MFExportOptions(root, PLATE_3MF)
        opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(opts)
        log.append(f"exported {PLATE_3MF}")
    if save:
        doc = app.activeDocument
        if doc.isSaved:
            doc.save(SAVE_NOTE)
            log.append(f"saved new version of '{doc.name}'")

    cam = app.activeViewport.camera
    cam.isSmoothTransition = False
    cam.target = adsk.core.Point3D.create(0, 0, 1.0)
    cam.eye = adsk.core.Point3D.create(6.0, -14.0, 12.0)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    app.activeViewport.camera = cam
    app.activeViewport.fit()
    return log


def run(context):
    for line in apply_layout(globals().get("LAYOUT_MODE", "print")):
        print(line)
