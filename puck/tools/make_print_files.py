#!/usr/bin/env python3
"""
Post-process the Fusion exports of Display-Puck GC9A01 into print-ready files.

Input : build_fusion/{Gehaeuse,Deckel,Klemmring}.{stl,step}  (from fusion/build_puck.py)
Output: STL/PUCK-*.stl      (print orientation, on Z=0)
        3MF/PUCK-alle-teile.3mf  (all parts on one plate)
        STEP/PUCK-alle-teile.step (assembled position, for Fusion import)

Also prints a mesh check (watertight, size, volume, filament estimate) and an
overhang analysis (> OVERHANG_LIMIT_DEG, ignoring the first layer and tiny areas).

Usage:  python3 tools/make_print_files.py
"""

from __future__ import annotations

import math
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "build_fusion"
STL_DIR = ROOT / "STL"
MF_DIR = ROOT / "3MF"
STEP_DIR = ROOT / "STEP"

PLA_DENSITY_G_CM3 = 1.24
INFILL_FACTOR = 0.45          # rough solid-fraction for 4 walls + 15 % gyroid
OVERHANG_LIMIT_DEG = 50.0     # steeper than this counts as "needs support"
OVERHANG_MIN_AREA_MM2 = 50.0  # short bridges (USB recess, 7 mm) and 1 mm ledges are fine
FIRST_LAYER_MM = 0.3
PLATE_GAP_MM = 8.0            # spacing between parts on the 3MF plate
PLATE_SIZE_MM = 256.0         # Bambu A1 / P1S

MM_PER_EXPORT_UNIT_CANDIDATES = (1.0, 10.0)  # Fusion STL may be mm or cm
EXPECTED_BODY_OD_MM = 64.0


@dataclass(frozen=True)
class Part:
    key: str          # Fusion export name
    out_name: str     # published file name
    flip: bool        # rotate 180° about X for printing


PARTS = (
    Part("Gehaeuse", "PUCK-Gehaeuse", flip=False),   # front face down
    Part("Deckel", "PUCK-Deckel", flip=True),        # outer face down
    Part("Klemmring", "PUCK-Klemmring", flip=False),
)


def load_mesh(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        raise ValueError(f"{path.name}: empty or invalid mesh")
    return mesh


def detect_scale(body: trimesh.Trimesh) -> float:
    """Return factor that converts the export unit to mm (checks the 62 mm OD)."""
    width = float(body.extents[0])
    for factor in MM_PER_EXPORT_UNIT_CANDIDATES:
        if abs(width * factor - EXPECTED_BODY_OD_MM) < 1.0:
            return factor
    raise ValueError(f"unexpected body width {width:.3f} - unit detection failed")


def to_print_pose(mesh: trimesh.Trimesh, flip: bool) -> trimesh.Trimesh:
    m = mesh.copy()
    if flip:
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    m.apply_translation([-m.bounds[0][0] - m.extents[0] / 2,
                         -m.bounds[0][1] - m.extents[1] / 2,
                         -m.bounds[0][2]])
    return m


def overhang_area(mesh: trimesh.Trimesh) -> float:
    """Downward-facing area steeper than the limit, above the first layer."""
    normals = mesh.face_normals
    centers = mesh.triangles_center
    limit = -math.cos(math.radians(90.0 - OVERHANG_LIMIT_DEG))  # n_z below this = overhang
    mask = (normals[:, 2] < limit) & (centers[:, 2] > FIRST_LAYER_MM)
    return float(mesh.area_faces[mask].sum())


def report(name: str, mesh: trimesh.Trimesh) -> None:
    vol_cm3 = mesh.volume / 1000.0
    grams = vol_cm3 * PLA_DENSITY_G_CM3 * INFILL_FACTOR
    ext = mesh.extents
    oh = overhang_area(mesh)
    flag = "OK" if oh < OVERHANG_MIN_AREA_MM2 else "CHECK"
    print(f"{name:18s} {ext[0]:6.2f} x {ext[1]:6.2f} x {ext[2]:6.2f} mm | "
          f"watertight={mesh.is_watertight} | vol {vol_cm3:5.2f} cm3 | ~{grams:4.1f} g PLA | "
          f"overhang>{OVERHANG_LIMIT_DEG:.0f}deg {oh:5.1f} mm2 [{flag}]")


THREEMF_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
THREEMF_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)


def _mesh_xml(obj_id: int, name: str, mesh: trimesh.Trimesh) -> str:
    verts = "".join(f'<vertex x="{v[0]:.4f}" y="{v[1]:.4f}" z="{v[2]:.4f}"/>' for v in mesh.vertices)
    tris = "".join(f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in mesh.faces)
    return (f'<object id="{obj_id}" name="{escape(name)}" type="model"><mesh>'
            f"<vertices>{verts}</vertices><triangles>{tris}</triangles></mesh></object>")


def write_3mf(meshes: dict[str, trimesh.Trimesh], path: Path) -> None:
    """Minimal 3MF core writer (one object per part, laid out in a row, plate-centred)."""
    widths = [m.extents[0] for m in meshes.values()]
    row = sum(widths) + PLATE_GAP_MM * (len(widths) - 1)
    if row > PLATE_SIZE_MM:
        raise ValueError("parts do not fit on one plate")
    x = PLATE_SIZE_MM / 2 - row / 2
    objects, items = [], []
    for obj_id, (name, mesh) in enumerate(meshes.items(), start=1):
        placed = mesh.copy()
        placed.apply_translation([x - placed.bounds[0][0],
                                  PLATE_SIZE_MM / 2 - placed.bounds[0][1] - placed.extents[1] / 2,
                                  -placed.bounds[0][2]])
        x += placed.extents[0] + PLATE_GAP_MM
        objects.append(_mesh_xml(obj_id, name, placed))
        items.append(f'<item objectid="{obj_id}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f"<resources>{''.join(objects)}</resources><build>{''.join(items)}</build></model>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", THREEMF_CONTENT_TYPES)
        zf.writestr("_rels/.rels", THREEMF_RELS)
        zf.writestr("3D/3dmodel.model", model)


def write_combined_step(path: Path) -> None:
    try:
        import cadquery as cq
    except ImportError:
        print("cadquery missing - combined STEP skipped")
        return
    assy = cq.Assembly(name="Display-Puck-GC9A01")
    for part in PARTS:
        shape = cq.importers.importStep(str(SRC_DIR / f"{part.key}.step"))
        assy.add(shape, name=part.key)
    assy.export(str(path), exportType="STEP")


def main() -> int:
    for d in (STL_DIR, MF_DIR, STEP_DIR):
        d.mkdir(exist_ok=True)
    try:
        raw = {p.key: load_mesh(SRC_DIR / f"{p.key}.stl") for p in PARTS}
        scale = detect_scale(raw["Gehaeuse"])
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    printed: dict[str, trimesh.Trimesh] = {}
    for part in PARTS:
        mesh = raw[part.key].copy()
        mesh.apply_scale(scale)
        mesh = to_print_pose(mesh, part.flip)
        mesh.export(STL_DIR / f"{part.out_name}.stl")
        printed[part.out_name] = mesh
        report(part.out_name, mesh)

    total = sum(m.volume for m in printed.values()) / 1000.0
    print(f"total ~{total * PLA_DENSITY_G_CM3 * INFILL_FACTOR:.0f} g PLA (estimate)")
    write_3mf(printed, MF_DIR / "PUCK-alle-teile.3mf")
    write_combined_step(STEP_DIR / "PUCK-alle-teile.step")
    for part in PARTS:
        (STEP_DIR / f"{part.out_name}.step").write_bytes((SRC_DIR / f"{part.key}.step").read_bytes())
    print(f"written: {STL_DIR.name}/, {MF_DIR.name}/, {STEP_DIR.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
