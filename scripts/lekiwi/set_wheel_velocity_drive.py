# Set LeKiwi wheel joints to velocity drive mode
# Run this in Isaac Sim Script Editor BEFORE pressing Play

from pxr import UsdPhysics, Usd

stage = omni.usd.get_context().get_stage()

# LeKiwi wheel joint paths
wheel_joints = [
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_2_Revolute_60",
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_1_Revolute_62",
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_Revolute_64",
]

for joint_path in wheel_joints:
    prim = stage.GetPrimAtPath(joint_path)
    if not prim.IsValid():
        print(f"[WARN] Joint not found: {joint_path}")
        continue

    # Get or create the drive
    drive = UsdPhysics.DriveAPI.Get(prim, "angular")
    if not drive:
        drive = UsdPhysics.DriveAPI.Apply(prim, "angular")

    # Set to velocity drive mode (not position)
    # High damping for velocity control, zero stiffness
    drive.GetDampingAttr().Set(1000.0)  # Velocity gain
    drive.GetStiffnessAttr().Set(0.0)   # No position control

    print(f"[OK] Set velocity drive: {joint_path}")

print("\n=== Wheel joints set to VELOCITY drive mode ===")
print("Now you can use teleop_wheel.sh without position errors!")
