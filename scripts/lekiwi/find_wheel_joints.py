# Find all wheel-related joints in LeKiwi
# Run this in Isaac Sim Script Editor

from pxr import Usd, UsdPhysics

stage = omni.usd.get_context().get_stage()

print("=" * 60)
print("Searching for wheel joints (ST3215_Servo_Motor)...")
print("=" * 60)

found_joints = []

for prim in stage.Traverse():
    prim_path = str(prim.GetPath())
    prim_name = prim.GetName()

    # Look for wheel motor joints
    if "ST3215_Servo_Motor" in prim_name or "Revolute_6" in prim_name:
        # Check if it's a joint
        if prim.HasAPI(UsdPhysics.RevoluteJoint) or "Revolute" in prim_name:
            found_joints.append(prim_path)
            print(f"Found: {prim_path}")

print()
print("=" * 60)
print(f"Total wheel joints found: {len(found_joints)}")
print("=" * 60)

if found_joints:
    print("\nCopy these paths to update the scripts:")
    for path in found_joints:
        print(f'    "{path}",')
