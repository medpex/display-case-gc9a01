"""
Interference check for Display-Puck GC9A01 (run inside Fusion on the built document).

Prints the intersection volume of every body pair. Expected: 0 mm3 everywhere
except Klemmring x Gehaeuse (intended press fit of the ring ribs).
Also shoots rays through the display window and the USB port: both must be free
(catches hidden "ghost plates" left over from boolean operations).
"""

import itertools
import os

import adsk.core
import adsk.fusion

VOLUME_TOLERANCE_MM3 = 0.05
EXPECTED_PRESS_FIT = {frozenset(("Klemmring", "Gehaeuse")),   # ring ribs, 0.2 press
                      frozenset(("Deckel", "Gehaeuse")),     # lip crush ribs + snap bead
                      frozenset(("Deckel", "Klemmring"))}    # hold-down posts, 0.3 preload
# (body name, ray origin mm, direction) -> ray must not hit that body
RAY_CHECKS = (
    ("Gehaeuse", (0.0, 0.0, -5.0), (0.0, 0.0, 1.0)),       # window axis, open to the rear
    ("Gehaeuse", (0.0, 12.0, -5.0), (0.0, 0.0, 1.0)),      # off-axis through the window
)
USB_RAY_BODY = "Deckel"
FUSION_DIR_FALLBACK = "/Users/jakob/Projekte/Display-Case-GC9A01/puck/fusion"
FUSION_DIR = (os.path.dirname(os.path.abspath(__file__))
              if "__file__" in globals() else FUSION_DIR_FALLBACK)
RAY_CONTROL = ("Gehaeuse", (0.0, 25.0, -5.0), (0.0, 0.0, 1.0))  # through the front wall: MUST hit


def _bodies(root):
    out = {}
    for occ in root.occurrences:
        for body in occ.bRepBodies:  # proxies in assembly context
            out[body.name] = body
    return out


def check():
    app = adsk.core.Application.get()
    root = adsk.fusion.Design.cast(app.activeProduct).rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    bodies = _bodies(root)
    lines = []
    for (na, a), (nb, b) in itertools.combinations(sorted(bodies.items()), 2):
        try:
            ta = tbm.copy(a)
            tb = tbm.copy(b)
            tbm.booleanOperation(ta, tb, adsk.fusion.BooleanTypes.IntersectionBooleanType)
            vol = ta.volume * 1000.0 if ta.faces.count else 0.0
        except Exception as exc:
            lines.append(f"ERR  {na} x {nb}: {exc}")
            continue
        if vol > VOLUME_TOLERANCE_MM3:
            tag = "FIT " if frozenset((na, nb)) in EXPECTED_PRESS_FIT else "HIT "
            lines.append(f"{tag} {na} x {nb}: {vol:.2f} mm3")
    lines.append(f"checked {len(bodies)} bodies")
    lines.extend(ray_checks(root, bodies))
    return lines


def _ray_hits(root, body, origin_mm, direction):
    """Faces of `body` hit by a ray (assembly coordinates, all occurrences at rest)."""
    origin = adsk.core.Point3D.create(*(v / 10.0 for v in origin_mm))
    faces = root.findBRepUsingRay(origin, adsk.core.Vector3D.create(*direction),
                                  adsk.fusion.BRepEntityTypes.BRepFaceEntityType, -1.0, False)
    return [f for f in faces if f.body.name == body.name]


def ray_checks(root, bodies):
    lines = []
    checks = list(RAY_CHECKS)
    ns = {}
    try:
        path = os.path.join(FUSION_DIR, "build_puck.py")
        ns["__file__"] = path
        with open(path, encoding="utf-8") as fh:
            exec(fh.read(), ns)
        checks.append((USB_RAY_BODY, (0.0, ns["USB_CY"], ns["DEPTH"] + 10.0), (0.0, 0.0, -1.0)))
    except Exception as exc:
        lines.append(f"ERR  USB ray setup: {exc}")
    for name, origin, direction in checks:
        body = bodies.get(name)
        if body is None:
            lines.append(f"ERR  ray: body {name} missing")
            continue
        hits = _ray_hits(root, body, origin, direction)
        tag = "RAY ok " if not hits else "RAY HIT"
        lines.append(f"{tag} {name} from {origin} dir {direction}: {len(hits)} face hits")
    name, origin, direction = RAY_CONTROL
    hits = _ray_hits(root, bodies[name], origin, direction) if name in bodies else []
    lines.append(f"{'CTRL ok ' if hits else 'CTRL FAIL'} control ray {name}: {len(hits)} face hits (expected > 0)")
    return lines


def run(context):
    for line in check():
        print(line)
