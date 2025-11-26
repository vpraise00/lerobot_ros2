# Check all LeKiwi joint positions for ±2π overflow
# Run this in Isaac Sim Script Editor

import math
from pxr import Usd, UsdPhysics, UsdGeom

stage = omni.usd.get_context().get_stage()

print("=" * 70)
print("LeKiwi Joint Positions (checking for ±2π overflow)")
print("=" * 70)

PI = math.pi
TWO_PI = 2 * PI

problem_joints = []

for prim in stage.Traverse():
    prim_path = str(prim.GetPath())

    # Only check LeKiwi joints
    if "/World/LeKiwi" not in prim_path:
        continue

    # Check if it has RevoluteJoint
    if prim.HasAPI(UsdPhysics.RevoluteJoint) or "Revolute" in prim.GetName():
        joint_name = prim.GetName()

        # Try to get current position from physics state
        # Note: This reads the USD attribute, not the live physics state
        drive = UsdPhysics.DriveAPI.Get(prim, "angular")
        if drive:
            target_attr = drive.GetTargetPositionAttr()
            if target_attr:
                target_pos = target_attr.Get()
                if target_pos is not None:
                    # Check if exceeds ±2π
                    status = "OK"
                    if abs(target_pos) > TWO_PI:
                        status = "OVERFLOW!"
                        problem_joints.append((joint_name, target_pos))
                    elif abs(target_pos) > PI:
                        status = "WARNING (>π)"

                    print(f"{joint_name}:")
                    print(f"  Target Position: {target_pos:.4f} rad ({math.degrees(target_pos):.2f} deg)")
                    print(f"  Status: {status}")
                    print()

print("=" * 70)
if problem_joints:
    print(f"PROBLEM JOINTS ({len(problem_joints)}):")
    for name, pos in problem_joints:
        print(f"  {name}: {pos:.4f} rad")
else:
    print("No joints exceeding ±2π found in USD attributes.")
    print("Note: Live physics state may differ from USD attributes.")
print("=" * 70)
