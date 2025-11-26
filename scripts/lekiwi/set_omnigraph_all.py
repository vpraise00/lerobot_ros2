"""
Unified Action Graph for LeKiwi in Isaac Sim.
- /joint_command: Arm position control (for MoveIt2)
- /wheel_command: Wheel velocity control (for teleop, no position to avoid ±2π errors)
- Joint state publish (/joint_states), TF (/tf), Clock (/clock), Cameras all included.

Run from Isaac Sim Script Editor:
    exec(open("/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_omnigraph_all.py").read())
"""

import omni.graph.core as og
import omni.usd
from pxr import Usd, UsdGeom, UsdPhysics, Sdf

GRAPH_PATH = "/World/LeKiwi/ActionGraph"
ARTICULATION_ROOT = "/World/LeKiwi"
ARM_CMD_TOPIC = "/joint_command"      # For MoveIt2 (position control)
WHEEL_CMD_TOPIC = "/wheel_command"    # For teleop (velocity only)
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
                ("ReadTime", "isaacsim.core.nodes.IsaacReadSystemTime"),
                ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
                ("PublishTF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),

                # Arm control - /joint_command (position control for MoveIt2)
                ("SubscribeArmCommand", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                ("ArmController", "isaacsim.core.nodes.IsaacArticulationController"),

                # Wheel control - /wheel_command (velocity only for teleop)
                ("SubscribeWheelCommand", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                ("WheelController", "isaacsim.core.nodes.IsaacArticulationController"),

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
                ("OnPlaybackTick.outputs:tick", "SubscribeArmCommand.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "SubscribeWheelCommand.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "ArmController.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "WheelController.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct1.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct2.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "PublishTF.inputs:execIn"),
                ("ReadTime.outputs:systemTime", "PublishTF.inputs:timeStamp"),

                # ROS2 Context for all nodes
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeArmCommand.inputs:context"),
                ("Context.outputs:context", "SubscribeWheelCommand.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),
                ("Context.outputs:context", "PublishTF.inputs:context"),
                ("Context.outputs:context", "CameraHelper1.inputs:context"),
                ("Context.outputs:context", "CameraHelper2.inputs:context"),

                # System time → timestamps
                ("ReadTime.outputs:systemTime", "PublishJointState.inputs:timeStamp"),
                ("ReadTime.outputs:systemTime", "PublishClock.inputs:timeStamp"),

                # Arm Controller - Full control (position, velocity, effort) for MoveIt2
                ("SubscribeArmCommand.outputs:jointNames", "ArmController.inputs:jointNames"),
                ("SubscribeArmCommand.outputs:positionCommand", "ArmController.inputs:positionCommand"),
                ("SubscribeArmCommand.outputs:velocityCommand", "ArmController.inputs:velocityCommand"),
                ("SubscribeArmCommand.outputs:effortCommand", "ArmController.inputs:effortCommand"),

                # Wheel Controller - Velocity only (NO positionCommand to avoid ±2π errors!)
                ("SubscribeWheelCommand.outputs:jointNames", "WheelController.inputs:jointNames"),
                # ("SubscribeWheelCommand.outputs:positionCommand", "WheelController.inputs:positionCommand"),  # DISABLED!
                ("SubscribeWheelCommand.outputs:velocityCommand", "WheelController.inputs:velocityCommand"),
                ("SubscribeWheelCommand.outputs:effortCommand", "WheelController.inputs:effortCommand"),

                # Camera 1 render product → ROS2 helper
                ("CreateRenderProduct1.outputs:execOut", "CameraHelper1.inputs:execIn"),
                ("CreateRenderProduct1.outputs:renderProductPath", "CameraHelper1.inputs:renderProductPath"),

                # Camera 2 render product → ROS2 helper
                ("CreateRenderProduct2.outputs:execOut", "CameraHelper2.inputs:execIn"),
                ("CreateRenderProduct2.outputs:renderProductPath", "CameraHelper2.inputs:renderProductPath"),
            ],
            og.Controller.Keys.SET_VALUES: [
                # Arm controller - /joint_command (for MoveIt2)
                ("ArmController.inputs:robotPath", robot_root_path),
                ("SubscribeArmCommand.inputs:topicName", ARM_CMD_TOPIC),

                # Wheel controller - /wheel_command (for teleop)
                ("WheelController.inputs:robotPath", robot_root_path),
                ("SubscribeWheelCommand.inputs:topicName", WHEEL_CMD_TOPIC),

                # Joint state publisher
                ("PublishJointState.inputs:targetPrim", robot_root_path),
                ("PublishJointState.inputs:topicName", JOINT_STATE_TOPIC),

                # Clock and TF
                ("PublishClock.inputs:topicName", "/clock"),
                ("PublishTF.inputs:topicName", "/tf"),
                ("Context.inputs:useDomainIDEnvVar", True),

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

    # Set PublishTF target prim
    try:
        tf_attr = og.Controller.attribute(f"{GRAPH_PATH}/PublishTF.inputs:targetPrims")
        if tf_attr is not None:
            og.Controller.set(tf_attr, [robot_root_path])
    except Exception:
        print("[LeKiwi Setup] Warning: PublishTF targetPrims attribute not found; set it manually if needed.")

    print("=" * 70)
    print(f"[LeKiwi Setup] Action Graph created at {GRAPH_PATH}")
    print("")
    print("  /joint_command  -> ArmController (position) for MoveIt2")
    print("  /wheel_command  -> WheelController (velocity only) for teleop")
    print("")
    print("  No more ±2π errors for continuous wheel rotation!")
    print("=" * 70)


if __name__ == "__main__":
    main()
