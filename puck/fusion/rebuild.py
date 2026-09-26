"""
Dev runner: closes the previous unsaved puck build, rebuilds and applies a view.

Set REBUILD_EXPORT / REBUILD_SAVE / REBUILD_VIEW in globals before exec'ing this file.
"""

import os

import adsk.core
import adsk.fusion

PROJECT_FUSION_DIR_FALLBACK = "/Users/jakob/Projekte/Display-Case-GC9A01/puck/fusion"
PROJECT_FUSION_DIR = (os.path.dirname(os.path.abspath(__file__))
                      if "__file__" in globals() else PROJECT_FUSION_DIR_FALLBACK)
MARKER_COMPONENT = "Gehaeuse"


def _close_previous_builds():
    app = adsk.core.Application.get()
    for doc in list(app.documents):
        try:
            prod = doc.products.itemByProductType("DesignProductType")
            des = adsk.fusion.Design.cast(prod)
            if (not doc.isSaved and des and des.rootComponent.occurrences.count
                    and des.rootComponent.occurrences.item(0).component.name == MARKER_COMPONENT):
                doc.close(False)
        except Exception as exc:
            print(f"skip document: {exc}")


def _load(name):
    path = os.path.join(PROJECT_FUSION_DIR, name)
    ns = {"__file__": path}
    with open(path, encoding="utf-8") as fh:
        exec(fh.read(), ns)
    return ns


def rebuild(export=False, save=False, view="hero"):
    _close_previous_builds()
    build_ns = _load("build_puck.py")
    build_ns["EXPORT"] = export
    build_ns["SAVE_TO_CLOUD"] = save
    for line in build_ns["build"]():
        print(line)
    if view:
        print(_load("view_puck.py")["apply_view"](view))


def run(context):
    rebuild(globals().get("REBUILD_EXPORT", False),
            globals().get("REBUILD_SAVE", False),
            globals().get("REBUILD_VIEW", "hero"))
