import omni.graph.core as og

og.Controller.edit(
    {
        "graph_path": "/World/LeKiwi/ActionGraph",  # 그래프를 만들 위치
        "evaluator_name": "execution",
    },
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
            ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
            ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ],
        og.Controller.Keys.CONNECT: [
            # exec 플로우
            ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),

            # 시뮬레이션 시간 → timestamp
            ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),

            # JointState → Articulation Controller
            ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
            ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
            ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
            ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
        ],
        og.Controller.Keys.SET_VALUES: [
            # LeKiwi prim 경로에 맞게 설정
            ("ArticulationController.inputs:robotPath", "/World/LeKiwi"),
            # PublishJointState는 아티큘레이션 루트 prim을 바라보게 한다.
            ("PublishJointState.inputs:targetPrim", "/World/LeKiwi"),
            # 필요하면 토픽명도 명시적으로 박을 수 있음
            ("PublishJointState.inputs:topicName", "/joint_states"),
            ("SubscribeJointState.inputs:topicName", "/joint_command"),
        ],
    },
)
