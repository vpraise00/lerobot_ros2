# Check LeKiwi wheel joint drive settings
# Run this in Isaac Sim Script Editor

from pxr import UsdPhysics, Usd

stage = omni.usd.get_context().get_stage()

# LeKiwi wheel joint paths
wheel_joints = [
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_2_Revolute_60",
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_1_Revolute_62",
    "/World/LeKiwi/joints/ST3215_Servo_Motor_v1_Revolute_64",
]

print("=" * 60)
print("LeKiwi Wheel Joint Drive Settings")
print("=" * 60)

for joint_path in wheel_joints:
    prim = stage.GetPrimAtPath(joint_path)
    if not prim.IsValid():
        print(f"[ERROR] Joint not found: {joint_path}")
        continue

    joint_name = joint_path.split("/")[-1]

    # Check angular drive
    drive = UsdPhysics.DriveAPI.Get(prim, "angular")
    if drive:
        stiffness = drive.GetStiffnessAttr().Get()
        damping = drive.GetDampingAttr().Get()

        # Velocity drive: stiffness=0, damping>0
        # Position drive: stiffness>0
        if stiffness == 0 and damping > 0:
            mode = "VELOCITY (OK)"
        elif stiffness > 0:
            mode = "POSITION (PROBLEM!)"
        else:
            mode = f"UNKNOWN (stiffness={stiffness}, damping={damping})"

        print(f"{joint_name}:")
        print(f"  Stiffness: {stiffness}")
        print(f"  Damping:   {damping}")
        print(f"  Mode:      {mode}")
    else:
        print(f"{joint_name}: No DriveAPI found")

    print()

print("=" * 60)
print("If any wheel shows 'POSITION (PROBLEM!)', run:")
print("exec(open('/home/vpraise/workspace/lerobot_ros2/scripts/lekiwi/set_wheel_velocity_drive.py').read())")
print("=" * 60)
