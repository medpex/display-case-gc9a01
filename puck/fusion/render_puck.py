"""
Write viewport renderings of Display-Puck GC9A01 to docs/img/render-<view>.png.

Run inside Fusion on the built document (after build_puck.py). Uses the camera
presets of view_puck.py; restores the assembled "hero" state at the end.
"""

import os

import adsk.core
import adsk.fusion

# Project root = parent of this fusion/ folder. Fusion's script runner sets __file__;
# when exec'd through the MCP bridge the caller puts __file__ into the namespace.
PROJECT_DIR_FALLBACK = "/Users/jakob/Projekte/Display-Case-GC9A01/puck"
PROJECT_DIR = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
               if "__file__" in globals() else PROJECT_DIR_FALLBACK)
IMG_DIR = os.path.join(PROJECT_DIR, "docs", "img")
VIEW_FILE = os.path.join(PROJECT_DIR, "fusion", "view_puck.py")
RENDER_VIEWS = ("hero", "front", "side", "rear", "exploded", "lid")
IMAGE_W = 2000
IMAGE_H = 1500
FINAL_VIEW = "hero"


def _load_views():
    ns = {}
    with open(VIEW_FILE, encoding="utf-8") as fh:
        exec(fh.read(), ns)
    return ns["apply_view"]


def render_all():
    app = adsk.core.Application.get()
    apply_view = _load_views()
    os.makedirs(IMG_DIR, exist_ok=True)
    written = []
    for name in RENDER_VIEWS:
        apply_view(name)
        path = os.path.join(IMG_DIR, f"render-{name}.png")
        opts = adsk.core.SaveImageFileOptions.create(path)
        opts.width = IMAGE_W
        opts.height = IMAGE_H
        opts.isBackgroundTransparent = True
        opts.isAntiAliased = True
        if not app.activeViewport.saveAsImageFileWithOptions(opts):
            raise RuntimeError(f"saving {path} failed")
        written.append(path)
    apply_view(FINAL_VIEW)
    return written


def run(context):
    for p in render_all():
        print("wrote", p)
