"""
Utility script for Isaac Sim Script Editor.

Creates Camera prims under the decorative mesh prims:
    /World/LeKiwi/Camera_Model_v3
    /World/LeKiwi/Camera_Model_v3_1

Idempotent: running multiple times will not duplicate existing cameras.
"""

from typing import Optional

import omni.usd
from pxr import Gf, Usd, UsdGeom

EXACT_LEKIWI_ROOT = "/World/LeKiwi"
ANCHOR_NAMES = ("Camera_Model_v3", "Camera_Model_v3_1")
CAMERA_NAME = "Camera"
CAMERA_TRANSFORMS = {
    "Camera_Model_v3": {
        "translate": Gf.Vec3f(-0.01, 0.01, 0.0),
        "rotateXYZ": Gf.Vec3f(90.0, 100.0, 0.0),
        "scale": Gf.Vec3f(1.0, 1.0, 1.0),
    },
    "Camera_Model_v3_1": {
        "translate": Gf.Vec3f(0.0, 0.0, 0.0),
        "rotateXYZ": Gf.Vec3f(-15.0, -120.0, 0.0),
        "scale": Gf.Vec3f(1.0, 1.0, 1.0),
    },
}

# Basic pinhole defaults (≈60 deg FOV at 640x480). Adjust if needed.
HORIZONTAL_APERTURE = 20.955  # mm
VERTICAL_APERTURE = 15.2908  # mm
FOCAL_LENGTH = 18.0  # mm
CLIP_RANGE = Gf.Vec2f(0.01, 200.0)
def _find_lekiwi_root(stage):
    """Return the prim that represents the LeKiwi root."""

    direct = stage.GetPrimAtPath(EXACT_LEKIWI_ROOT)
    if direct.IsValid():
        print(f"[LeKiwi Cameras] Found LeKiwi root at {EXACT_LEKIWI_ROOT}.")
        return direct

    world = stage.GetPrimAtPath("/World")
    if not world.IsValid():
        print("[LeKiwi Cameras] /World prim is missing. Cannot proceed.")
        return None

    for prim in Usd.PrimRange(world):
        if prim == world:
            continue
        if "lekiwi" in prim.GetName().lower():
            print(f"[LeKiwi Cameras] Detected LeKiwi root candidate: {prim.GetPath()}")
            return prim

    print("[LeKiwi Cameras] LeKiwi root prim not found under /World.")
    return None


def _find_anchor_prims(root_prim):
    anchors = {}
    for prim in Usd.PrimRange(root_prim):
        name = prim.GetName()
        if name in ANCHOR_NAMES:
            anchors[name] = prim
            print(f"[LeKiwi Cameras] Found anchor {name} at {prim.GetPath()}.")
    return anchors


def ensure_camera(stage, anchor_prim, anchor_name: str) -> Optional[str]:
    camera_path = anchor_prim.GetPath().AppendChild(CAMERA_NAME)
    camera_path_str = camera_path.pathString
    camera_prim = stage.GetPrimAtPath(camera_path)
    if camera_prim.IsValid():
        print(f"[LeKiwi Cameras] Camera already exists at {camera_path_str}.")
    else:
        stage.DefinePrim(camera_path, "Camera")
        camera = UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
        # TODO: adjust aperture/focal length if you need different resolution/FOV.
        camera.CreateHorizontalApertureAttr(HORIZONTAL_APERTURE)
        camera.CreateVerticalApertureAttr(VERTICAL_APERTURE)
        camera.CreateFocalLengthAttr(FOCAL_LENGTH)
        camera.CreateClippingRangeAttr(CLIP_RANGE)
        camera.CreateFocusDistanceAttr(1.0)
        camera.CreateProjectionAttr("perspective")

        print(
            f"[LeKiwi Cameras] Created camera at {camera_path_str}. "
            "See TODO if you need to fine-tune resolution/FOV."
        )
        camera_prim = stage.GetPrimAtPath(camera_path)

    _apply_camera_adjustments(camera_prim, anchor_name, camera_path_str)
    return camera_path_str


def _apply_camera_adjustments(camera_prim, anchor_name: str, camera_path: str) -> None:
    # hide the actual camera prim in viewport
    camera_prim.GetAttribute("visibility").Set("invisible")

    settings = CAMERA_TRANSFORMS.get(anchor_name)
    if settings is None:
        return

    xformable = UsdGeom.Xformable(camera_prim)
    for op in xformable.GetOrderedXformOps():
        xformable.RemoveXformOp(op)
    xformable.ClearXformOpOrder()

    translate_op = xformable.AddTranslateOp()
    translate_op.Set(settings["translate"])

    rotate_op = xformable.AddRotateXYZOp()
    rotate_op.Set(settings["rotateXYZ"])

    scale_op = xformable.AddScaleOp()
    scale_op.Set(settings["scale"])

    print(
        f"[LeKiwi Cameras] Adjusted transform for {anchor_name} "
        f"(translate={tuple(settings['translate'])}, rotate={tuple(settings['rotateXYZ'])}, "
        f"scale={tuple(settings['scale'])})."
    )

    ops = [op.GetOpName() for op in xformable.GetOrderedXformOps()]
    print(f"[LeKiwi Cameras] Final XformOps for {camera_path}: {ops}")


def main():
    usd_context = omni.usd.get_context()
    stage = usd_context.get_stage()
    if stage is None:
        print("[LeKiwi Cameras] No USD stage detected. Load your scene first.")
        return

    lekiwi_root = _find_lekiwi_root(stage)
    if lekiwi_root is None:
        return

    anchors = _find_anchor_prims(lekiwi_root)
    if len(anchors) == 0:
        print(
            f"[LeKiwi Cameras] Camera_Model_v3/_1 anchors not found under {lekiwi_root.GetPath()}."
        )
        return

    camera_paths = []
    for name in ANCHOR_NAMES:
        anchor = anchors.get(name)
        if anchor is None:
            print(f"[LeKiwi Cameras] Anchor {name} missing under {lekiwi_root.GetPath()}.")
            continue
        created = ensure_camera(stage, anchor, name)
        if created:
            camera_paths.append(created)

    if camera_paths:
        joined = ", ".join(camera_paths)
        print(f"[LeKiwi Cameras] Attached cameras: {joined}")
    else:
        print("[LeKiwi Cameras] No cameras could be attached.")


if __name__ == "__main__":
    main()
