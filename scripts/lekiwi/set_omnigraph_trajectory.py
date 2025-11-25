import omni.graph.core as og

"""
Action Graph builder for LeKiwi that listens to ROS2 JointTrajectory commands.

Use when MoveIt (or any FollowJointTrajectory client) publishes to
/joint_trajectory_controller/joint_trajectory. This graph does not include the
JointState teleop subscriber – use set_omnigraph_jointstate.py for manual commands.
"""

TARGET_ARTICULATION = "/World/LeKiwi"
TARGET_ROOT_PRIM = "/World/LeKiwi"
GRAPH_PATH = f"{TARGET_ARTICULATION}/ActionGraph"

og.Controller.edit(
    {
        "graph_path": GRAPH_PATH,
        "evaluator_name": "execution",
    },
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
            ("SubscribeJointTrajectory", "isaacsim.ros2.bridge.ROS2SubscribeJointTrajectory"),
            ("TrajectoryPlayer", "isaacsim.core.nodes.IsaacArticulationTrajectory"),
            ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
        ],
        og.Controller.Keys.CONNECT: [
            # Execution flow
            ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "SubscribeJointTrajectory.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "TrajectoryPlayer.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),

            # Simulation time → JointState timestamp
            ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),

            # JointTrajectory → Trajectory player → Controller
            ("SubscribeJointTrajectory.outputs:jointTrajectory", "TrajectoryPlayer.inputs:jointTrajectory"),
            ("TrajectoryPlayer.outputs:jointNames", "ArticulationController.inputs:jointNames"),
            ("TrajectoryPlayer.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
            ("TrajectoryPlayer.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
            ("TrajectoryPlayer.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
        ],
        og.Controller.Keys.SET_VALUES: [
            # JointState 퍼블리시는 아티큘레이션 루트 prim을 가리키게 한다.
            ("PublishJointState.inputs:targetPrim", TARGET_ROOT_PRIM),
            ("PublishJointState.inputs:topicName", "/joint_states"),
            ("SubscribeJointTrajectory.inputs:topicName", "/joint_trajectory_controller/joint_trajectory"),
            ("TrajectoryPlayer.inputs:robotPath", TARGET_ARTICULATION),
            ("ArticulationController.inputs:robotPath", TARGET_ARTICULATION),
        ],
    },
)
