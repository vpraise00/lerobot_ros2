import omni.graph.core as og
import omni.usd
from typing import List

from pxr import Usd, UsdGeom

GRAPH_PATH = "/World/LeKiwi/CameraGraph"
CAMERA_ROOT = "/World/LeKiwi"
IMAGE_TOPIC = "/lekiwi/camera/front/image_raw"
FRAME_ID = "lekiwi_camera_front_optical_frame"
PREFERRED_CAMERA_PATHS = [
    "/World/LeKiwi/Camera_Model_v3/Camera",
    "/World/LeKiwi/Camera_Model_v3_1/Camera",
]
ANCHOR_NAMES = ("Camera_Model_v3", "Camera_Model_v3_1")
EXACT_LEKIWI_ROOT = "/World/LeKiwi"


def _find_lekiwi_root(stage):
    direct = stage.GetPrimAtPath(EXACT_LEKIWI_ROOT)
    if direct.IsValid():
        return direct

    world = stage.GetPrimAtPath("/World")
    if not world.IsValid():
        print("[LeKiwi Camera Graph] /World prim missing while searching for LeKiwi root.")
        return None

    for prim in Usd.PrimRange(world):
        if prim == world:
            continue
        if "lekiwi" in prim.GetName().lower():
            print(f"[LeKiwi Camera Graph] Using LeKiwi root candidate {prim.GetPath()} for camera lookup.")
            return prim
    print("[LeKiwi Camera Graph] Could not locate a LeKiwi root under /World.")
    return None


def _collect_preferred_paths(stage) -> List[str]:
    seen = []
    for path in PREFERRED_CAMERA_PATHS:
        if path not in seen:
            seen.append(path)

    root = _find_lekiwi_root(stage)
    if root is not None:
        for prim in Usd.PrimRange(root):
            name = prim.GetName()
            if name in ANCHOR_NAMES:
                candidate = prim.GetPath().AppendChild("Camera").pathString
                if candidate not in seen:
                    seen.append(candidate)
    return seen


def _resolve_camera(stage) -> str:
    preferred_paths = _collect_preferred_paths(stage)
    preferred_found = []
    for path in preferred_paths:
        prim = stage.GetPrimAtPath(path)
        is_valid = prim.IsValid() and prim.IsA(UsdGeom.Camera)
        preferred_found.append((path, is_valid))
        state = "FOUND" if is_valid else "missing"
        print(f"[LeKiwi Camera Graph] Preferred camera {path}: {state}")

    valid_preferred = [path for path, ok in preferred_found if ok]
    if valid_preferred:
        if len(valid_preferred) > 1:
            print(
                "[LeKiwi Camera Graph] Multiple preferred cameras detected. "
                "Only the first will be wired for now."
            )
        selected = valid_preferred[0]
        print(f"[LeKiwi Camera Graph] Using preferred camera: {selected}")
        if len(valid_preferred) > 1:
            print(f"[LeKiwi Camera Graph] Second candidate available: {valid_preferred[1]}")
        return selected

    print(
        "[LeKiwi Camera Graph] Preferred camera paths not found. "
        "Falling back to the first camera under /World/LeKiwi."
    )

    root_prim = stage.GetPrimAtPath(CAMERA_ROOT)
    if not root_prim.IsValid():
        raise RuntimeError(f"Prim '{CAMERA_ROOT}' not found. Make sure LeKiwi is in the scene.")

    for prim in Usd.PrimRange(root_prim):
        if prim.IsA(UsdGeom.Camera):
            selected = prim.GetPath().pathString
            print(f"[LeKiwi Camera Graph] Fallback camera selected: {selected}")
            return selected

    raise RuntimeError("Could not find any Camera prims under /World/LeKiwi.")


def build_camera_graph() -> None:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is loaded. Load your scene before running this script.")

    camera_prim_path = _resolve_camera(stage)

    og.Controller.edit(
        {"graph_path": GRAPH_PATH, "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("CreateRenderProduct", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
                ("CameraHelper", "isaacsim.ros2.bridge.ROS2CameraHelper"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct.inputs:execIn"),
                ("CreateRenderProduct.outputs:execOut", "CameraHelper.inputs:execIn"),
                ("CreateRenderProduct.outputs:renderProductPath", "CameraHelper.inputs:renderProductPath"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("CreateRenderProduct.inputs:cameraPrim", camera_prim_path),
                ("CreateRenderProduct.inputs:width", 1280),
                ("CreateRenderProduct.inputs:height", 720),
                ("CameraHelper.inputs:topicName", IMAGE_TOPIC),
                ("CameraHelper.inputs:frameId", FRAME_ID),
                ("CameraHelper.inputs:semanticLabelsTopicName", "/lekiwi/camera/front/semantic"),
            ],
        },
    )

    print(
        "[LeKiwi Camera Graph] Created Action Graph at "
        f"{GRAPH_PATH}. Remember to enable isaacsim.ros2.bridge first."
    )


if __name__ == "__main__":
    build_camera_graph()
