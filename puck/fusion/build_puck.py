"""
Display-Puck GC9A01 — parametric Fusion model (Autodesk Fusion Python API)

Round, 15°-tilted desk "puck" for a GC9A01 1.28" round TFT + ESP32-C3 Super Mini.
Variant of "Display-Case GC9A01" (MakerWorld 3082754); the display mount (window,
glass seat, module pocket, pins, clamp ring) is copied 1:1 from the test-printed
original CASE-FINAL.step.

Run:   Fusion -> Utilities -> Scripts and Add-Ins -> + -> this file -> Run
       (or via the Fusion MCP bridge). Always builds into a NEW document.

Coordinates (all parts share them, assembled position):
  origin = display centre on the front face, +Y = display "up", +Z = to the rear.
  The whole puck is later tilted by TILT_DEG; the foot plane is horizontal in the
  tilted frame.

Print orientation (no supports):
  Gehaeuse   front face down (as modelled, +Z up)
  Deckel     outer face down (flip Z)
  Klemmring  flat

Fusion stores lengths in cm internally; all constants here are mm, cm() converts.
"""

import math
import os
import traceback

import adsk.core
import adsk.fusion

# ============================================================================
# Parameters (mm / degrees)
# ============================================================================

# --- Puck shell -------------------------------------------------------------
PUCK_OD = 64.0            # outer diameter (bore r=30 clears the module tab corners r=29.16)
WALL = 2.0                # radial wall
DEPTH = 34.0              # body depth (front face -> rear face, without lid)
FRONT_T = 1.7             # front wall thickness (same as original)
TILT_DEG = 15.0           # backward tilt of the display face

# --- Foot (integrated wedge below the cylinder) ------------------------------
FOOT_W = 34.0             # foot width (X)
FOOT_TOP_Y = -24.0        # upper edge of the foot sketch (buried in the shell)
FOOT_SLOPE_DEG = 45.0     # front slope of the foot (printable overhang)
FOOT_CLEAR = 0.5          # lid rim clearance above the table
FOOT_FILLET = 1.5         # fillet around the foot pad

# --- Display mount (1:1 from original CASE-FINAL.step) -----------------------
WINDOW_D = 34.0           # visible window
SEAT_D = 36.0             # glass seat
SEAT_Z1 = 3.5             # glass seat ends here (from front face)
POCKET_D = 39.0           # module pocket
BOSS_D = 41.0             # boss outer diameter
BOSS_Z = 8.0              # boss rear end
BOSS_GAP_W = 26.0         # opening towards the chin / FPC (down, -Y)
BOSS_GAP_Y_TOP = -10.0    # upper edge of the opening cut
PIN_D = 1.5               # locating pins beside the chin
PIN_X = 9.45
PIN_Y = -20.97
PIN_Z = 5.5
WINDOW_CHAMFER = 0.8      # bezel chamfer on the window
FRONT_CHAMFER = 1.0       # outer front edge (bed side -> chamfer, no fillet)
REAR_FILLET = 1.2         # outer rear rim of the body

# --- Clamp ring (1:1 from original incl. its press-fit ribs) -------------------
RING_OD = 38.6
RING_ID = 32.8
RING_T = 2.2
RING_GAP_W = 15.0         # FPC opening in the ring
RING_FLAT_Y = -17.78      # ring is flattened below this (clears tab / FPC)
RING_RIB_ANGLES_DEG = (90.0, 210.0, 330.0)
RING_RIB_W = 4.0          # ribs on the ring, hull 39.2 in pocket 39.0 -> 0.2 press
RING_RIB_R = 19.6

# --- Lid snap / key -------------------------------------------------------------
COVER_T = 2.0             # lid plate thickness
LIP_H = 5.0               # lip reaching into the bore (v2: 3.0 -> longer guidance)
LIP_CLEAR = 0.10          # radial clearance lip <-> bore (v2: 0.25 was wobbly)
LIP_RIB_ANGLES_DEG = (22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5)
LIP_RIB_W = 1.0           # crush ribs on the lip, tangential width
LIP_RIB_H = 0.20          # beyond the lip -> 0.1 mm interference in the bore
LIP_RIB_LEAD = 0.8        # ribs stop this far before the lip tip (lead-in)
LIP_WALL = 1.2
SNAP_FROM_REAR = 1.5      # snap bead/groove centre, measured from rear face
BEAD_H = 0.30             # bead height beyond lip (0.20 interference)
BEAD_HALF = 0.50          # half-height of the 45° bead
GROOVE_DEPTH = 0.50       # groove depth into the bore wall
GROOVE_HALF = 0.70
LIP_SLOT_W = 1.5          # flex slots in the lip
LIP_SLOT_ANGLES_DEG = (0.0, 180.0, 270.0)
KEY_ANGLE_DEG = 90.0      # anti-rotation key at the top
KEY_W = 3.0
KEY_RADIAL = 1.1
KEY_LEN = 3.2
KEY_SLOT_W = 3.6
COVER_CHAMFER = 0.8

# --- Display hold-down posts on the lid (press on the clamp ring) ------------
POST_ANGLES_DEG = (30.0, 90.0, 150.0)  # clear of the ESP32 sled and the ring ribs at 210/330
POST_R = 17.3             # post centre radius (on the ring face, clear of the ribs)
POST_D = 5.0              # post diameter above the boss
POST_TIP_D = 3.0          # post tip diameter inside the module pocket
POST_TIP_START = 8.6      # tip begins here (boss rear end is at 8.0)
POST_PRELOAD = 0.3        # tip reaches this far into the ring's rear face (lid plate flexes)

# --- ESP32-C3 Super Mini holder (on the lid, board perpendicular) ------------
ESP_W = 18.0              # board width
ESP_L = 22.6              # board length (measured 22.6; datasheet 22.52)
PCB_T = 1.2               # ASSUMPTION: board thickness (measure!)
ESP_Y0 = -13.0            # board bottom face (Y)
SLOT_CLEAR = 0.15
# v2 sled: rigid U-channel (walls + floor) + flat snap tongue under the board.
SLED_WALL = 2.5           # wall thickness outside the board edge (X)
LEDGE_WRAP = 0.8          # bottom ledge under the board edge (clear of solder joints)
TOP_LIP_WRAP = 0.3        # tiny top lip over the board edge (clears pin headers)
TOP_LIP_T = 1.2
FLOOR_GAP = 1.8           # floor below the board (bottom solder joints)
FLOOR_T = 1.6
TONGUE_W = 7.0            # snap tongue under the board centre (no pins there)
TONGUE_T = 1.4
TONGUE_SLIT = 0.4         # gap tongue <-> floor
NUB_H = 0.65              # nub rises above the board bottom face -> hook engagement
NUB_TOP = 0.8             # flat top of the nub
TONGUE_TAIL = 0.3         # tongue continues beyond the nub ramp
HOOK_GAP = 0.2            # play between board end and hook face
RAIL_ROOT = 0.5           # sled reaches into the lid plate

# --- USB-C port ---------------------------------------------------------------
USB_W = 8.94
USB_H = 3.26
USB_L = 7.35
USB_OVERHANG = 1.2        # receptacle sticks out beyond the PCB end
USB_HOLE_CLEAR = 0.3      # per side
USB_RECESS_W = 12.6       # outer recess for the plug overmould
USB_RECESS_H = 7.0
USB_RECESS_D = 1.0

# --- Reference parts (render only, never exported for print) ----------------
GLASS_D = 35.6
GLASS_T = 1.6
MODULE_PCB_D = 38.03      # measured (MSP1281 module)
MODULE_PCB_T = 1.6
MODULE_TAB_W = 23.0      # measured 22.95
MODULE_TAB_Y = (-26.8, -15.0)  # tab reaches 7.8 below the round PCB
MODULE_HOLE_D = 2.0       # mounting holes = locating pins

# --- Appearances (German Fusion library names) --------------------------------
APPEARANCE_LIBRARY = "Fusion-Darstellungsbibliothek"
APPEAR_BODY = "Kunststoff - matt (Weiß)"
APPEAR_RING = "Kunststoff - matt (Grau)"
APPEAR_GLASS = "Kunststoff - glänzend (Schwarz)"
APPEAR_PCB = "Farbe - Emaille glänzend (Blau)"
APPEAR_USB = "Edelstahl - satiniert"

# --- Names / output -------------------------------------------------------------
DOC_NAME = "Display-Puck GC9A01"
COMP_BODY = "Gehaeuse"
COMP_COVER = "Deckel"
COMP_RING = "Klemmring"
COMP_REF = "Referenz Display (nicht drucken)"
COMP_REF_ESP = "Referenz ESP32 (nicht drucken)"
# Project root = parent of this fusion/ folder. Fusion's script runner sets __file__;
# when exec'd through the MCP bridge the caller puts __file__ into the namespace.
PROJECT_DIR_FALLBACK = "/Users/jakob/Projekte/Display-Case-GC9A01/puck"
PROJECT_DIR = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
               if "__file__" in globals() else PROJECT_DIR_FALLBACK)
EXPORT = True             # write STEP/STL/F3D to PROJECT_DIR/build_fusion
SAVE_TO_CLOUD = True      # save the document into FUSION_PROJECT
FUSION_PROJECT = "Design"
REUSE_SAVED_DOCUMENT = True  # rebuild into the open cloud document if present
SAVE_VERSION_NOTE = "Rebuild via fusion/build_puck.py"
EXPORT_SUBDIR = "build_fusion"

EPS = 0.01                # overlap to avoid coincident faces

# ============================================================================
# Derived values
# ============================================================================
R_OUT = PUCK_OD / 2.0
R_IN = R_OUT - WALL
TILT = math.radians(TILT_DEG)
SNAP_Z = DEPTH - SNAP_FROM_REAR
LIP_R_OUT = R_IN - LIP_CLEAR
LIP_R_IN = LIP_R_OUT - LIP_WALL
USB_CY = ESP_Y0 + PCB_T + USB_H / 2.0

# Foot plane: world height h = y*cos(t) - z*sin(t). The lowest point of the lid rim
# (y=-R_OUT, z=DEPTH+COVER_T) must stay FOOT_CLEAR above the table.
FOOT_H = R_OUT * math.cos(TILT) + (DEPTH + COVER_T) * math.sin(TILT) + FOOT_CLEAR


def foot_plane_y(z: float) -> float:
    """Local Y of the (horizontal) foot plane at local depth z."""
    return (-FOOT_H + z * math.sin(TILT)) / math.cos(TILT)


def foot_slope_z() -> float:
    """Depth where the 45° front slope of the foot meets the foot plane."""
    k = math.tan(math.radians(FOOT_SLOPE_DEG))
    # FOOT_TOP_Y - k*z == foot_plane_y(z)
    return (FOOT_TOP_Y * math.cos(TILT) + FOOT_H) / (k * math.cos(TILT) + math.sin(TILT))


# ============================================================================
# Helpers
# ============================================================================
def cm(v_mm: float) -> float:
    return v_mm / 10.0


def pt(x: float, y: float, z: float = 0.0) -> adsk.core.Point3D:
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def val(v_mm: float) -> adsk.core.ValueInput:
    return adsk.core.ValueInput.createByReal(cm(v_mm))


class PartBuilder:
    """Thin wrapper around one Fusion component with sketch/extrude helpers."""

    def __init__(self, comp: adsk.fusion.Component):
        self.comp = comp
        self._planes = {}

    # --- construction planes -------------------------------------------------
    def _offset_plane(self, base, offset_mm: float, axis: str, label: str):
        key = (axis, round(offset_mm, 4))
        if key in self._planes:
            return self._planes[key]
        if abs(offset_mm) < 1e-9:
            self._planes[key] = base
            return base
        planes = self.comp.constructionPlanes
        for sign in (1.0, -1.0):
            inp = planes.createInput()
            inp.setByOffset(base, val(sign * offset_mm))
            pl = planes.add(inp)
            origin = pl.geometry.origin
            got = {"x": origin.x, "y": origin.y, "z": origin.z}[axis] * 10.0
            if abs(got - offset_mm) < 1e-4:
                pl.name = f"{label}={offset_mm:g}"
                pl.isLightBulbOn = False
                self._planes[key] = pl
                return pl
            pl.deleteMe()
        raise RuntimeError(f"offset plane {label}={offset_mm} could not be created")

    def plane_xy(self, z: float):
        return self._offset_plane(self.comp.xYConstructionPlane, z, "z", "Z")

    def plane_xz(self, y: float):
        return self._offset_plane(self.comp.xZConstructionPlane, y, "y", "Y")

    def plane_yz(self):
        return self.comp.yZConstructionPlane

    # --- sketches ----------------------------------------------------------------
    def sketch(self, plane, name: str) -> adsk.fusion.Sketch:
        sk = self.comp.sketches.add(plane)
        sk.name = name
        sk.isComputeDeferred = True
        return sk

    @staticmethod
    def _sp(sk, x, y, z):
        return sk.modelToSketchSpace(pt(x, y, z))

    def circle(self, sk, cx, cy, cz, r):
        sk.sketchCurves.sketchCircles.addByCenterRadius(self._sp(sk, cx, cy, cz), cm(r))

    def polygon(self, sk, pts3d):
        lines = sk.sketchCurves.sketchLines
        sp = [self._sp(sk, *p) for p in pts3d]
        for i in range(len(sp)):
            lines.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])

    def rect_xy(self, sk, x0, x1, y0, y1, z):
        self.polygon(sk, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])

    def rotated_rect_xy(self, sk, ang_deg, r0, r1, w, z):
        """Rectangle radial from r0 to r1, width w, rotated to ang_deg (XY)."""
        a = math.radians(ang_deg)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        h = w / 2.0
        corners = [(r0, -h), (r1, -h), (r1, h), (r0, h)]
        self.polygon(sk, [(r * ux + s * vx, r * uy + s * vy, z) for r, s in corners])

    def stadium_xy(self, sk, cx, cy, w, h, z):
        """Slot shape as rectangle + 2 end circles (all profiles are used)."""
        r = h / 2.0
        self.rect_xy(sk, cx - w / 2 + r, cx + w / 2 - r, cy - r, cy + r, z)
        self.circle(sk, cx - w / 2 + r, cy, z, r)
        self.circle(sk, cx + w / 2 - r, cy, z, r)

    @staticmethod
    def profiles(sk):
        sk.isComputeDeferred = False
        coll = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            coll.add(sk.profiles.item(i))
        if coll.count == 0:
            raise RuntimeError(f"sketch '{sk.name}' has no closed profile")
        return coll

    # --- features ----------------------------------------------------------------
    def extrude(self, sk, dist_mm, op, bodies=None, symmetric=False, name=None):
        feats = self.comp.features.extrudeFeatures
        inp = feats.createInput(self.profiles(sk), op)
        if symmetric:
            inp.setSymmetricExtent(val(abs(dist_mm)), True)
        else:
            direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if dist_mm >= 0
                         else adsk.fusion.ExtentDirections.NegativeExtentDirection)
            inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(val(abs(dist_mm))),
                                 direction)
        if bodies is not None:
            inp.participantBodies = list(bodies)
        feat = feats.add(inp)
        if name:
            feat.name = name
        return feat

    def revolve_z(self, sk, op, bodies=None, name=None):
        feats = self.comp.features.revolveFeatures
        inp = feats.createInput(self.profiles(sk), self.comp.zConstructionAxis, op)
        inp.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
        if bodies is not None:
            inp.participantBodies = list(bodies)
        feat = feats.add(inp)
        if name:
            feat.name = name
        return feat


NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


# --- edge finishing ------------------------------------------------------------------
def planar_face(body, z_mm: float, normal_z_sign: float, min_area_mm2: float = 50.0):
    """Largest planar face lying in z=z_mm whose outward normal points to sign."""
    best = None
    for face in body.faces:
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        p = face.pointOnFace
        if abs(p.z * 10.0 - z_mm) > 1e-3:
            continue
        ok, n = face.evaluator.getNormalAtPoint(p)
        if not ok or n.z * normal_z_sign < 0.99:
            continue
        area = face.area * 100.0
        if area >= min_area_mm2 and (best is None or area > best.area * 100.0):
            best = face
    return best


def loop_edges(face, outer: bool):
    coll = adsk.core.ObjectCollection.create()
    for loop in face.loops:
        if loop.isOuter == outer:
            for e in loop.edges:
                coll.add(e)
    return coll


def circle_edges(body, radius_mm: float, z_mm: float):
    coll = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if g.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
            if abs(g.radius * 10.0 - radius_mm) < 1e-3 and abs(g.center.z * 10.0 - z_mm) < 1e-3:
                coll.add(e)
    return coll


def fillet(comp, edges, r_mm: float, name: str, log: list):
    if edges is None or edges.count == 0:
        log.append(f"WARN fillet {name}: no edges")
        return
    feats = comp.features.filletFeatures
    for radius in (r_mm, r_mm * 0.6):
        try:
            inp = feats.createInput()
            try:
                inp.edgeSetInputs.addConstantRadiusEdgeSet(edges, val(radius), True)
            except AttributeError:
                inp.addConstantRadiusEdgeSet(edges, val(radius), True)
            f = feats.add(inp)
            f.name = name
            log.append(f"fillet {name} R{radius:g} on {edges.count} edges")
            return
        except Exception as exc:  # geometry may reject the radius
            log.append(f"WARN fillet {name} R{radius:g} failed: {exc}")


def chamfer(comp, edges, d_mm: float, name: str, log: list):
    if edges is None or edges.count == 0:
        log.append(f"WARN chamfer {name}: no edges")
        return
    feats = comp.features.chamferFeatures
    try:
        inp = feats.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, val(d_mm), True)
        f = feats.add(inp)
        f.name = name
        log.append(f"chamfer {name} {d_mm:g} on {edges.count} edges")
    except Exception as exc:
        log.append(f"WARN chamfer {name} failed: {exc}")


# ============================================================================
# Parts
# ============================================================================
def build_body(b: PartBuilder, log: list):
    # 1) cylinder
    sk = b.sketch(b.plane_xy(0.0), "Zylinder")
    b.circle(sk, 0, 0, 0, R_OUT)
    body = b.extrude(sk, DEPTH, NEW, name="Zylinder").bodies.item(0)
    body.name = COMP_BODY

    # 2) foot: YZ profile, extruded symmetric in X
    zs = foot_slope_z()
    sk = b.sketch(b.plane_yz(), "Fuss")
    b.polygon(sk, [
        (0, FOOT_TOP_Y, 0.0),
        (0, foot_plane_y(zs), zs),
        (0, foot_plane_y(DEPTH), DEPTH),
        (0, FOOT_TOP_Y, DEPTH),
    ])
    b.extrude(sk, FOOT_W, JOIN, [body], symmetric=True, name="Fuss")
    log.append(f"foot: H={FOOT_H:.2f} slope ends z={zs:.2f}, "
               f"pad y front={foot_plane_y(zs):.2f} rear={foot_plane_y(DEPTH):.2f}")

    # 3) cavity
    sk = b.sketch(b.plane_xy(FRONT_T), "Innenraum")
    b.circle(sk, 0, 0, FRONT_T, R_IN)
    b.extrude(sk, DEPTH - FRONT_T + EPS, CUT, [body], name="Innenraum")

    # 4) window
    sk = b.sketch(b.plane_xy(0.0), "Fenster")
    b.circle(sk, 0, 0, 0, WINDOW_D / 2)
    b.extrude(sk, FRONT_T, CUT, [body], name="Fenster")

    # 5) boss + seat + pocket
    sk = b.sketch(b.plane_xy(FRONT_T), "Boss")
    b.circle(sk, 0, 0, FRONT_T, BOSS_D / 2)
    b.extrude(sk, BOSS_Z - FRONT_T, JOIN, [body], name="Boss")

    sk = b.sketch(b.plane_xy(FRONT_T), "Glassitz")
    b.circle(sk, 0, 0, FRONT_T, SEAT_D / 2)
    b.extrude(sk, SEAT_Z1 - FRONT_T, CUT, [body], name="Glassitz")

    sk = b.sketch(b.plane_xy(SEAT_Z1), "Modultasche")
    b.circle(sk, 0, 0, SEAT_Z1, POCKET_D / 2)
    b.extrude(sk, BOSS_Z - SEAT_Z1 + EPS, CUT, [body], name="Modultasche")

    sk = b.sketch(b.plane_xy(FRONT_T), "Kinn-Oeffnung")
    b.rect_xy(sk, -BOSS_GAP_W / 2, BOSS_GAP_W / 2, -BOSS_D / 2 - 0.5, BOSS_GAP_Y_TOP, FRONT_T)
    b.extrude(sk, BOSS_Z - FRONT_T + EPS, CUT, [body], name="Kinn-Oeffnung")

    # 6) locating pins
    sk = b.sketch(b.plane_xy(FRONT_T), "Stifte")
    for sx in (-1.0, 1.0):
        b.circle(sk, sx * PIN_X, PIN_Y, FRONT_T, PIN_D / 2)
    b.extrude(sk, PIN_Z - FRONT_T, JOIN, [body], name="Stifte")

    # 7) snap groove for the lid (revolved 45° V)
    sk = b.sketch(b.plane_xz(0.0), "Rastnut")
    b.polygon(sk, [
        (R_IN - 0.1, 0, SNAP_Z - GROOVE_HALF - 0.1),
        (R_IN + GROOVE_DEPTH, 0, SNAP_Z),
        (R_IN - 0.1, 0, SNAP_Z + GROOVE_HALF + 0.1),
    ])
    b.revolve_z(sk, CUT, [body], name="Rastnut")

    # 8) anti-rotation key (after the groove, stays intact)
    sk = b.sketch(b.plane_xy(DEPTH), "Verdrehsicherung")
    b.rotated_rect_xy(sk, KEY_ANGLE_DEG, R_IN - KEY_RADIAL, R_IN + 0.3, KEY_W, DEPTH)
    b.extrude(sk, -KEY_LEN, JOIN, [body], name="Verdrehsicherung")

    # 9) edges
    comp = b.comp
    rear = planar_face(body, DEPTH, +1.0, min_area_mm2=300.0)
    if rear:
        fillet(comp, loop_edges(rear, outer=True), REAR_FILLET, "Rueckkante", log)
    pad = None
    for face in body.faces:  # foot pad = planar face whose normal is world-down
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        ok, n = face.evaluator.getNormalAtPoint(face.pointOnFace)
        if ok and abs(n.y + math.cos(TILT)) < 1e-3 and abs(n.z - math.sin(TILT)) < 1e-3:
            pad = face
    if pad:
        fillet(comp, loop_edges(pad, outer=True), FOOT_FILLET, "Fusskante", log)
    else:
        log.append("WARN foot pad face not found")
    chamfer(comp, circle_edges(body, R_OUT, 0.0), FRONT_CHAMFER, "Frontfase", log)
    chamfer(comp, circle_edges(body, WINDOW_D / 2, 0.0), WINDOW_CHAMFER, "Fensterfase", log)
    return body


def build_cover(b: PartBuilder, log: list):
    # plate
    sk = b.sketch(b.plane_xy(DEPTH), "Deckelplatte")
    b.circle(sk, 0, 0, DEPTH, R_OUT)
    body = b.extrude(sk, COVER_T, NEW, name="Deckelplatte").bodies.item(0)
    body.name = COMP_COVER

    # lip
    sk = b.sketch(b.plane_xy(DEPTH), "Kragen")
    b.circle(sk, 0, 0, DEPTH, LIP_R_OUT)
    b.extrude(sk, -LIP_H, JOIN, [body], name="Kragen")
    sk = b.sketch(b.plane_xy(DEPTH), "Kragen-innen")
    b.circle(sk, 0, 0, DEPTH, LIP_R_IN)
    b.extrude(sk, -(LIP_H + EPS), CUT, [body], name="Kragen-innen")

    # snap bead
    sk = b.sketch(b.plane_xz(0.0), "Rastwulst")
    b.polygon(sk, [
        (LIP_R_OUT - 0.1, 0, SNAP_Z - BEAD_HALF),
        (LIP_R_OUT + BEAD_H, 0, SNAP_Z),
        (LIP_R_OUT - 0.1, 0, SNAP_Z + BEAD_HALF),
    ])
    b.revolve_z(sk, JOIN, [body], name="Rastwulst")

    # flex slots + key slot
    sk = b.sketch(b.plane_xy(DEPTH), "Kragen-Schlitze")
    for ang in LIP_SLOT_ANGLES_DEG:
        b.rotated_rect_xy(sk, ang, LIP_R_IN - 0.5, R_OUT - 0.5, LIP_SLOT_W, DEPTH)
    b.rotated_rect_xy(sk, KEY_ANGLE_DEG, LIP_R_IN - 0.5, R_OUT - 0.5, KEY_SLOT_W, DEPTH)
    b.extrude(sk, -(LIP_H + EPS), CUT, [body], name="Kragen-Schlitze")

    # crush ribs on the lip (snug fit, no wobble)
    sk = b.sketch(b.plane_xy(DEPTH), "Kragen-Rippen")
    for ang in LIP_RIB_ANGLES_DEG:
        b.rotated_rect_xy(sk, ang, LIP_R_OUT - 0.2, LIP_R_OUT + LIP_RIB_H, LIP_RIB_W, DEPTH)
    b.extrude(sk, -(LIP_H - LIP_RIB_LEAD), JOIN, [body], name="Kragen-Rippen")

    # display hold-down posts: press the clamp ring from behind
    ring_back = SEAT_Z1 + MODULE_PCB_T + RING_T
    z_tip = ring_back - POST_PRELOAD
    sk = b.sketch(b.plane_xy(DEPTH), "Niederhalter")
    for ang in POST_ANGLES_DEG:
        px, py = POST_R * math.cos(math.radians(ang)), POST_R * math.sin(math.radians(ang))
        b.circle(sk, px, py, DEPTH, POST_D / 2)
    b.extrude(sk, -(DEPTH - POST_TIP_START), JOIN, [body], name="Niederhalter")
    sk = b.sketch(b.plane_xy(POST_TIP_START), "Niederhalter-Spitzen")
    for ang in POST_ANGLES_DEG:
        px, py = POST_R * math.cos(math.radians(ang)), POST_R * math.sin(math.radians(ang))
        b.circle(sk, px, py, POST_TIP_START, POST_TIP_D / 2)
    b.extrude(sk, -(POST_TIP_START - z_tip), JOIN, [body], name="Niederhalter-Spitzen")
    log.append(f"hold-down posts: tip z={z_tip:.2f} (ring back {ring_back:.2f})")

    # ESP32 sled: rigid U-channel profile (XY), extruded from the plate inwards
    y0 = ESP_Y0
    y_bot = y0 - FLOOR_GAP - FLOOR_T
    y_top = y0 + PCB_T + SLOT_CLEAR + TOP_LIP_T
    x_edge = ESP_W / 2.0 + SLOT_CLEAR
    x_out = x_edge + SLED_WALL
    z_hook = DEPTH - (ESP_L + HOOK_GAP)
    z_root = DEPTH + RAIL_ROOT
    sk = b.sketch(b.plane_xy(z_root), "ESP-Schlitten")
    for sx in (-1.0, 1.0):
        rects = [
            (x_edge, x_out, y_bot, y_top),                                   # outer wall
            (ESP_W / 2.0 - LEDGE_WRAP, x_edge, y_bot, y0 - SLOT_CLEAR),       # bottom ledge
            (ESP_W / 2.0 - TOP_LIP_WRAP, x_edge, y0 + PCB_T + SLOT_CLEAR, y_top),  # top lip
            (TONGUE_W / 2.0 + TONGUE_SLIT, x_edge, y_bot, y0 - FLOOR_GAP),   # floor half
        ]
        for xa, xb, ya, yb in rects:
            x0, x1 = sorted((sx * xa, sx * xb))
            b.rect_xy(sk, x0, x1, ya, yb, z_root)
    b.extrude(sk, -(z_root - z_hook), JOIN, [body], name="ESP-Schlitten")

    # snap tongue (flat, under the board centre) with hook nub at its tip
    ramp = NUB_H + SLOT_CLEAR                    # 45° ramp height = run
    z_tongue_tip = z_hook - NUB_TOP - ramp - TONGUE_TAIL
    sk = b.sketch(b.plane_xy(z_root), "ESP-Zunge")
    b.rect_xy(sk, -TONGUE_W / 2.0, TONGUE_W / 2.0, y0 - SLOT_CLEAR - TONGUE_T, y0 - SLOT_CLEAR, z_root)
    b.extrude(sk, -(z_root - z_tongue_tip), JOIN, [body], name="ESP-Zunge")
    sk = b.sketch(b.plane_yz(), "ESP-Rastnase")
    b.polygon(sk, [
        (0, y0 - SLOT_CLEAR - 0.1, z_hook),
        (0, y0 + NUB_H, z_hook),
        (0, y0 + NUB_H, z_hook - NUB_TOP),
        (0, y0 - SLOT_CLEAR - 0.1, z_hook - NUB_TOP - ramp),
    ])
    b.extrude(sk, TONGUE_W, JOIN, [body], symmetric=True, name="ESP-Rastnase")
    log.append(f"ESP sled: hook face z={z_hook:.2f}, tongue {z_root - z_tongue_tip:.1f} mm")

    # USB-C hole + outer recess
    sk = b.sketch(b.plane_xy(DEPTH), "USB-C")
    b.stadium_xy(sk, 0, USB_CY, USB_W + 2 * USB_HOLE_CLEAR, USB_H + 2 * USB_HOLE_CLEAR, DEPTH)
    b.extrude(sk, COVER_T + RAIL_ROOT, CUT, [body], name="USB-C")
    sk = b.sketch(b.plane_xy(DEPTH + COVER_T), "USB-C-Senkung")
    b.stadium_xy(sk, 0, USB_CY, USB_RECESS_W, USB_RECESS_H, DEPTH + COVER_T)
    b.extrude(sk, -USB_RECESS_D, CUT, [body], name="USB-C-Senkung")

    chamfer(b.comp, circle_edges(body, R_OUT, DEPTH + COVER_T), COVER_CHAMFER, "Deckelfase", log)
    return body


def build_ring(b: PartBuilder, log: list):
    z0 = SEAT_Z1 + MODULE_PCB_T   # real seat: pressed onto the display PCB back
    sk = b.sketch(b.plane_xy(z0), "Ring")
    b.circle(sk, 0, 0, z0, RING_OD / 2)
    body = b.extrude(sk, RING_T, NEW, name="Ring").bodies.item(0)
    body.name = COMP_RING
    sk = b.sketch(b.plane_xy(z0), "Ring-innen")
    b.circle(sk, 0, 0, z0, RING_ID / 2)
    b.extrude(sk, RING_T, CUT, [body], name="Ring-innen")
    sk = b.sketch(b.plane_xy(z0), "Ring-Rippen")
    for ang in RING_RIB_ANGLES_DEG:
        b.rotated_rect_xy(sk, ang, RING_OD / 2 - 0.4, RING_RIB_R, RING_RIB_W, z0)
    b.extrude(sk, RING_T, JOIN, [body], name="Ring-Rippen")
    sk = b.sketch(b.plane_xy(z0), "Ring-FPC")
    b.rect_xy(sk, -RING_GAP_W / 2, RING_GAP_W / 2, -RING_OD / 2 - 1.0, -RING_ID / 2 + 2.0, z0)
    b.extrude(sk, RING_T, CUT, [body], name="Ring-FPC")
    sk = b.sketch(b.plane_xy(z0), "Ring-Abflachung")
    b.rect_xy(sk, -RING_OD / 2 - 1.0, RING_OD / 2 + 1.0, -RING_OD / 2 - 1.0, RING_FLAT_Y, z0)
    b.extrude(sk, RING_T, CUT, [body], name="Ring-Abflachung")
    log.append("ring built")
    return body


def build_reference(b: PartBuilder, b_esp: PartBuilder, log: list):
    bodies = {}
    sk = b.sketch(b.plane_xy(FRONT_T), "Ref-Glas")
    b.circle(sk, 0, 0, FRONT_T, GLASS_D / 2)
    bodies["glass"] = b.extrude(sk, GLASS_T, NEW, name="Ref-Glas").bodies.item(0)
    bodies["glass"].name = "GC9A01 Glas"

    z_pcb = SEAT_Z1
    sk = b.sketch(b.plane_xy(z_pcb), "Ref-Modul")
    b.circle(sk, 0, 0, z_pcb, MODULE_PCB_D / 2)
    b.rect_xy(sk, -MODULE_TAB_W / 2, MODULE_TAB_W / 2, MODULE_TAB_Y[0], MODULE_TAB_Y[1], z_pcb)
    bodies["module"] = b.extrude(sk, MODULE_PCB_T, NEW, name="Ref-Modul").bodies.item(0)
    bodies["module"].name = "GC9A01 Platine"
    sk = b.sketch(b.plane_xy(z_pcb), "Ref-Modul-Loecher")
    for sx in (-1.0, 1.0):
        b.circle(sk, sx * PIN_X, PIN_Y, z_pcb, MODULE_HOLE_D / 2)
    b.extrude(sk, MODULE_PCB_T, CUT, [bodies["module"]], name="Ref-Modul-Loecher")

    y_esp = ESP_Y0 + PCB_T / 2
    sk = b_esp.sketch(b_esp.plane_xz(y_esp), "Ref-ESP")
    b_esp.polygon(sk, [(-ESP_W / 2, y_esp, DEPTH - ESP_L), (ESP_W / 2, y_esp, DEPTH - ESP_L),
                   (ESP_W / 2, y_esp, DEPTH), (-ESP_W / 2, y_esp, DEPTH)])
    bodies["esp"] = b_esp.extrude(sk, PCB_T, NEW, symmetric=True, name="Ref-ESP").bodies.item(0)
    bodies["esp"].name = "ESP32-C3 Super Mini"

    z_usb = DEPTH + USB_OVERHANG - USB_L   # receptacle is a stadium like the real part
    sk = b_esp.sketch(b_esp.plane_xy(z_usb), "Ref-USB")
    b_esp.stadium_xy(sk, 0, USB_CY, USB_W, USB_H, z_usb)
    bodies["usb"] = b_esp.extrude(sk, USB_L, NEW, name="Ref-USB").bodies.item(0)
    bodies["usb"].name = "USB-C Buchse"
    log.append("reference parts built")
    return bodies


# ============================================================================
# Document level
# ============================================================================
def add_user_parameters(design):
    params = [
        ("PUCK_OD", PUCK_OD, "Aussendurchmesser Puck"),
        ("WALL", WALL, "Wandstaerke radial"),
        ("DEPTH", DEPTH, "Gehaeusetiefe ohne Deckel"),
        ("FRONT_T", FRONT_T, "Frontwand"),
        ("FOOT_W", FOOT_W, "Fussbreite"),
        ("COVER_T", COVER_T, "Deckelplatte"),
        ("LIP_H", LIP_H, "Rastkragen Hoehe"),
        ("LIP_CLEAR", LIP_CLEAR, "Spiel Kragen/Bohrung radial"),
        ("PCB_T", PCB_T, "ESP32-C3 Platinendicke (Annahme)"),
        ("RING_T", RING_T, "Klemmring Dicke"),
    ]
    for name, v, comment in params:
        existing = design.userParameters.itemByName(name)
        expr = f"{v:g} mm"
        if existing:
            existing.expression = expr
        else:
            design.userParameters.add(name, adsk.core.ValueInput.createByString(expr), "mm", comment)
    tilt = design.userParameters.itemByName("TILT")
    if not tilt:
        design.userParameters.add("TILT", adsk.core.ValueInput.createByString(f"{TILT_DEG:g} deg"),
                                  "deg", "Kippwinkel Displayflaeche")


def appearance(app, design, name):
    lib = app.materialLibraries.itemByName(APPEARANCE_LIBRARY)
    if lib is None:
        return None
    local = design.appearances.itemByName(name)
    if local:
        return local
    src = lib.appearances.itemByName(name)
    return design.appearances.addByCopy(src, name) if src else None


def paint(app, design, body, name, log):
    try:
        a = appearance(app, design, name)
        if a:
            body.appearance = a
        else:
            log.append(f"WARN appearance '{name}' not found")
    except Exception as exc:
        log.append(f"WARN appearance '{name}': {exc}")


def find_saved_document(app):
    """Open, cloud-saved puck document (reused so rebuilds become new versions)."""
    if not REUSE_SAVED_DOCUMENT:
        return None
    for doc in app.documents:
        if doc.isSaved and doc.name.startswith(DOC_NAME):
            return doc
    return None


def clear_design(design):
    root = design.rootComponent
    for occ in list(root.occurrences):
        occ.deleteMe()
    for sk in list(root.sketches):
        sk.deleteMe()


def new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ


def export_all(app, design, occs: dict, log: list):
    out = os.path.join(PROJECT_DIR, EXPORT_SUBDIR)
    os.makedirs(out, exist_ok=True)
    em = design.exportManager
    for key in (COMP_BODY, COMP_COVER, COMP_RING):
        occ = occs[key]
        body = occ.component.bRepBodies.item(0)
        stl = em.createSTLExportOptions(body, os.path.join(out, f"{key}.stl"))
        stl.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        stl.isBinaryFormat = True
        em.execute(stl)
        stp = em.createSTEPExportOptions(os.path.join(out, f"{key}.step"), occ.component)
        em.execute(stp)
        log.append(f"exported {key}")
    f3d = em.createFusionArchiveExportOptions(os.path.join(out, "Display-Puck-GC9A01.f3d"))
    em.execute(f3d)
    log.append(f"exported f3d -> {out}")


def report(occs: dict, log: list):
    for key, occ in occs.items():
        for body in occ.component.bRepBodies:
            bb = body.boundingBox
            dims = [(bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
                    (bb.maxPoint.z - bb.minPoint.z) * 10]
            vol = body.volume * 1000.0
            log.append(f"{key}/{body.name}: bbox {dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f} mm, "
                       f"vol {vol:.0f} mm3, solid={body.isSolid}")


def build():
    app = adsk.core.Application.get()
    log = []
    doc = find_saved_document(app)
    if doc:  # rebuild in place -> new version of the same cloud file
        doc.activate()
        design = adsk.fusion.Design.cast(app.activeProduct)
        clear_design(design)
        log.append(f"rebuilding in saved document '{doc.name}'")
    else:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    add_user_parameters(design)

    occs = {}
    for key, fn in ((COMP_BODY, build_body), (COMP_COVER, build_cover), (COMP_RING, build_ring)):
        occ = new_component(root, key)
        fn(PartBuilder(occ.component), log)
        occs[key] = occ
    ref_occ = new_component(root, COMP_REF)
    ref_esp_occ = new_component(root, COMP_REF_ESP)
    ref = build_reference(PartBuilder(ref_occ.component), PartBuilder(ref_esp_occ.component), log)

    paint(app, design, occs[COMP_BODY].component.bRepBodies.item(0), APPEAR_BODY, log)
    paint(app, design, occs[COMP_COVER].component.bRepBodies.item(0), APPEAR_BODY, log)
    paint(app, design, occs[COMP_RING].component.bRepBodies.item(0), APPEAR_RING, log)
    paint(app, design, ref["glass"], APPEAR_GLASS, log)
    paint(app, design, ref["module"], APPEAR_PCB, log)
    paint(app, design, ref["esp"], APPEAR_PCB, log)
    paint(app, design, ref["usb"], APPEAR_USB, log)

    report({**occs, COMP_REF: ref_occ, COMP_REF_ESP: ref_esp_occ}, log)
    if EXPORT:
        export_all(app, design, occs, log)
    if SAVE_TO_CLOUD:
        try:  # activeProject can be unavailable -> resolve the project by name
            if doc.isSaved and doc.dataFile:
                doc.save(SAVE_VERSION_NOTE)
                log.append(f"saved new version of '{doc.name}'")
                app.activeViewport.fit()
                return log
            hub = app.data.activeHub
            project = next((hub.dataProjects.item(i) for i in range(hub.dataProjects.count)
                            if hub.dataProjects.item(i).name == FUSION_PROJECT), None)
            if project is None:
                raise RuntimeError(f"Fusion project '{FUSION_PROJECT}' not found")
            doc.saveAs(DOC_NAME, project.rootFolder, "Round 15° desk puck for GC9A01 + ESP32-C3", "")
            log.append(f"saved to Fusion project '{FUSION_PROJECT}'")
        except Exception as exc:
            log.append(f"WARN cloud save failed: {exc}")
    app.activeViewport.fit()
    return log


def run(context):
    try:
        for line in build():
            print(line)
    except Exception:
        print("FAILED:\n" + traceback.format_exc())
        raise
