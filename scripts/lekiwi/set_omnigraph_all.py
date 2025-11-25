"""
Unified Action Graph for LeKiwi in Isaac Sim (single graph).
- Joint command/state bridge (JointState on /joint_command → Articulation; /joint_states publish).
- Two cameras → ROS2CameraHelper:
    /lekiwi/camera/front/image_raw  (Camera_Model_v3)
    /lekiwi/camera/rear/image_raw   (Camera_Model_v3_1)

Prereq: Run set_lekiwi_cameras.py once so Camera prims exist under LeKiwi anchors.

Run from Isaac Sim Script Editor (absolute path recommended):
    exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())
"""

import omni.graph.core as og
import omni.usd
from pxr import Usd, UsdGeom, UsdPhysics, Sdf
from pxr import UsdPhysics

GRAPH_PATH = "/World/LeKiwi/ActionGraph"
ARTICULATION_ROOT = "/World/LeKiwi"  # fallback default
JOINT_CMD_TOPIC = "/joint_command"
JOINT_STATE_TOPIC = "/joint_states"

CAMERAS = [
    {
        "anchor": "Camera_Model_v3",
        "topic": "/lekiwi/camera/base/image_raw",
        "frame": "lekiwi_camera_base_optical_frame",
    },
    {
        "anchor": "Camera_Model_v3_1",
        "topic": "/lekiwi/camera/wrist/image_raw",
        "frame": "lekiwi_camera_wrist_optical_frame",
    },
]


def _find_lekiwi_root(stage):
    """Find the LeKiwi articulation root prim (auto-detect path)."""
    direct = stage.GetPrimAtPath(ARTICULATION_ROOT)
    if direct.IsValid():
        return direct
    world = stage.GetPrimAtPath("/World")
    if not world.IsValid():
        print("[LeKiwi Setup] /World prim missing while searching for LeKiwi root.")
        return None
    for prim in Usd.PrimRange(world):
        if prim == world:
            continue
        if "lekiwi" in prim.GetName().lower() and prim.IsA(UsdGeom.Xform):
            print(f"[LeKiwi Setup] Using LeKiwi root candidate {prim.GetPath()} for lookup.")
            return prim
    print("[LeKiwi Setup] Could not locate a LeKiwi root under /World.")
    return None


def _ensure_articulation_root(root_prim):
    """Apply/enable PhysX articulation root API on the prim."""
    try:
        api = UsdPhysics.ArticulationRootAPI.Apply(root_prim)
        if hasattr(api, "CreateEnabledAttr"):
            api.CreateEnabledAttr(True)
        else:
            # Fallback: set attribute manually
            attr = root_prim.CreateAttribute("physics:articulation:enabled", Sdf.ValueTypeNames.Bool)
            attr.Set(True)
        print(f"[LeKiwi Setup] Enabled ArticulationRootAPI on {root_prim.GetPath()}.")
    except Exception as exc:
        print(f"[LeKiwi Setup] Failed to set ArticulationRootAPI on {root_prim.GetPath()}: {exc}")


def _resolve_camera(stage, root, anchor_name: str) -> str:
    preferred = []
    if root is not None:
        for prim in Usd.PrimRange(root):
            if prim.GetName() == anchor_name:
                preferred.append(prim.GetPath().AppendChild("Camera").pathString)

    for path in preferred:
        prim = stage.GetPrimAtPath(path)
        ok = prim.IsValid() and prim.IsA(UsdGeom.Camera)
        print(f"[LeKiwi Setup] Camera {anchor_name} at {path}: {'FOUND' if ok else 'missing'}")
        if ok:
            return path

    # Fallback: any camera under LeKiwi
    if root is None:
        raise RuntimeError("Cannot find LeKiwi root; set the robot prim under /World.")
    for prim in Usd.PrimRange(root):
        if prim.IsA(UsdGeom.Camera):
            fallback = prim.GetPath().pathString
            print(f"[LeKiwi Setup] Fallback camera for {anchor_name}: {fallback}")
            return fallback

    raise RuntimeError(f"No Camera prims found for anchor {anchor_name}. Run set_lekiwi_cameras.py first.")


def main() -> None:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is loaded. Load your scene before running this script.")

    root = _find_lekiwi_root(stage)
    if root is None:
        raise RuntimeError("LeKiwi root prim not found. Ensure the robot is under /World.")
    robot_root_path = root.GetPath().pathString
    print(f"[LeKiwi Setup] Using robot root: {robot_root_path}")

    _ensure_articulation_root(root)

    camera_prim_paths = []
    for cam in CAMERAS:
        path = _resolve_camera(stage, root, cam["anchor"])
        camera_prim_paths.append((path, cam))

    og.Controller.edit(
        {"graph_path": GRAPH_PATH, "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("ReadTime", "isaacsim.core.nodes.IsaacReadSystemTime"),  # Use wall-clock to match ROS nodes by default
                ("Context", "isaacsim.ros2.bridge.ROS2Context"),  # Explicit ROS2 context so discovery is deterministic
                ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
                ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
                ("PublishTF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
                # Camera 1
                ("CreateRenderProduct1", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
                ("CameraHelper1", "isaacsim.ros2.bridge.ROS2CameraHelper"),
                # Camera 2
                ("CreateRenderProduct2", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
                ("CameraHelper2", "isaacsim.ros2.bridge.ROS2CameraHelper"),
            ],
            og.Controller.Keys.CONNECT: [
                # Tick flow
                ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct1.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct2.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "PublishTF.inputs:execIn"),
                ("ReadTime.outputs:systemTime", "PublishTF.inputs:timeStamp"),

                # Tie all ROS nodes to the same context (Domain ID / RMW)
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),
                ("Context.outputs:context", "PublishTF.inputs:context"),
                ("Context.outputs:context", "CameraHelper1.inputs:context"),
                ("Context.outputs:context", "CameraHelper2.inputs:context"),

                # System time → timestamps
                ("ReadTime.outputs:systemTime", "PublishJointState.inputs:timeStamp"),
                ("ReadTime.outputs:systemTime", "PublishClock.inputs:timeStamp"),

                # JointState → Articulation
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
                ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),

                # Camera 1 render product → ROS2 helper
                ("CreateRenderProduct1.outputs:execOut", "CameraHelper1.inputs:execIn"),
                ("CreateRenderProduct1.outputs:renderProductPath", "CameraHelper1.inputs:renderProductPath"),

                # Camera 2 render product → ROS2 helper
                ("CreateRenderProduct2.outputs:execOut", "CameraHelper2.inputs:execIn"),
                ("CreateRenderProduct2.outputs:renderProductPath", "CameraHelper2.inputs:renderProductPath"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("ArticulationController.inputs:robotPath", robot_root_path),
                ("PublishJointState.inputs:targetPrim", robot_root_path),
                ("PublishJointState.inputs:topicName", JOINT_STATE_TOPIC),
                ("SubscribeJointState.inputs:topicName", JOINT_CMD_TOPIC),
                ("PublishClock.inputs:topicName", "/clock"),
                ("PublishTF.inputs:topicName", "/tf"),
                ("Context.inputs:useDomainIDEnvVar", True),  # Follow ROS_DOMAIN_ID from environment

                # Camera 1
                ("CreateRenderProduct1.inputs:cameraPrim", camera_prim_paths[0][0]),
                ("CreateRenderProduct1.inputs:width", 1280),
                ("CreateRenderProduct1.inputs:height", 720),
                ("CameraHelper1.inputs:topicName", CAMERAS[0]["topic"]),
                ("CameraHelper1.inputs:frameId", CAMERAS[0]["frame"]),
                ("CameraHelper1.inputs:semanticLabelsTopicName", "/lekiwi/camera/base/semantic"),

                # Camera 2
                ("CreateRenderProduct2.inputs:cameraPrim", camera_prim_paths[1][0]),
                ("CreateRenderProduct2.inputs:width", 1280),
                ("CreateRenderProduct2.inputs:height", 720),
                ("CameraHelper2.inputs:topicName", CAMERAS[1]["topic"]),
                ("CameraHelper2.inputs:frameId", CAMERAS[1]["frame"]),
                ("CameraHelper2.inputs:semanticLabelsTopicName", "/lekiwi/camera/wrist/semantic"),
            ],
        },
    )

    # Try to set PublishTF target prim if the attribute exists (Isaac versions differ on the input name)
    try:
        tf_attr = og.Controller.attribute(f"{GRAPH_PATH}/PublishTF.inputs:targetPrims")
        if tf_attr is not None:
            og.Controller.set(tf_attr, [robot_root_path])
    except Exception:
        print("[LeKiwi Setup] Warning: PublishTF targetPrims attribute not found; set it manually if needed.")

    print(f"[LeKiwi Setup] Unified Action Graph with dual cameras created at {GRAPH_PATH}. Press Play to start.")


if __name__ == "__main__":
    main()
