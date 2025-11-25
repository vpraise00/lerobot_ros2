#!/usr/bin/env python3
"""
Isaac Sim Omnigraph Setup Script for LeKiwi

Automatically creates and configures the ROS2 action graph for LeKiwi robot.
This script should be run inside Isaac Sim Python environment.

Usage (inside Isaac Sim):
    python setup_omnigraph.py

Features:
- Creates ROS2 action graph for joint control
- Configures publish/subscribe topics
- Sets up articulation controller
- Publishes clock for sim time
- Configures QoS profiles for reliable communication
"""

import omni.graph.core as og
import omni.kit.commands


def create_ros2_action_graph():
    """Create complete ROS2 action graph for LeKiwi robot."""

    print("Creating ROS2 Action Graph for LeKiwi...")

    # Create action graph
    (result, (graph, nodes, _, _)) = og.Controller.edit(
        {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                # ROS2 Context - shared context for all ROS2 nodes
                ("Context", "omni.isaac.ros2_bridge.ROS2Context"),

                # Subscribe to joint commands from ROS2
                ("SubscribeJointState", "omni.isaac.ros2_bridge.ROS2SubscribeJointState"),

                # Articulation controller to apply commands to robot
                ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),

                # Publish joint states to ROS2
                ("PublishJointState", "omni.isaac.ros2_bridge.ROS2PublishJointState"),

                # Publish clock for simulation time
                ("PublishClock", "omni.isaac.ros2_bridge.ROS2PublishClock"),

                # On playback tick - triggers graph execution
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ],

            og.Controller.Keys.CONNECT: [
                # Connect playback tick to all nodes that need regular updates
                ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),

                # Connect subscribe to articulation controller
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
                ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
            ],

            og.Controller.Keys.SET_VALUES: [
                # ROS2 Context settings
                ("Context.inputs:domain_id", 10),  # Match ROS_DOMAIN_ID

                # Subscribe JointState settings
                ("SubscribeJointState.inputs:topicName", "/joint_command"),
                ("SubscribeJointState.inputs:qosProfile", "RELIABLE"),  # Match Isaac Sim QoS

                # Articulation Controller settings
                # Note: targetPrim must be set manually in UI or via code to point to robot root
                # Example: /World/LeKiwi/base_plate_layer1_v5

                # Publish JointState settings
                ("PublishJointState.inputs:topicName", "/joint_states"),
                ("PublishJointState.inputs:qosProfile", "RELIABLE"),  # Changed from BEST_EFFORT

                # Publish Clock settings
                ("PublishClock.inputs:topicName", "/clock"),
            ],
        },
    )

    if result:
        print("✅ Action graph created successfully!")
        print("\n⚠️  Manual steps required:")
        print("1. Select ArticulationController node")
        print("2. Set 'targetPrim' to your robot root prim (e.g., /World/LeKiwi)")
        print("3. Select PublishJointState node")
        print("4. Set 'targetPrim' to your robot root prim (e.g., /World/LeKiwi)")
        print("\nGraph configuration:")
        print("  - ROS_DOMAIN_ID: 10")
        print("  - Subscribe: /joint_command (RELIABLE)")
        print("  - Publish: /joint_states (RELIABLE)")
        print("  - Publish: /clock")
        return True
    else:
        print("❌ Failed to create action graph")
        return False


def verify_omnigraph_setup():
    """Verify that the omnigraph is set up correctly."""
    print("\nVerifying omnigraph setup...")

    try:
        graph = og.Controller.graph("/ActionGraph")
        if graph is None:
            print("❌ Action graph not found")
            return False

        print("✅ Action graph exists")

        # Check for required nodes
        required_nodes = [
            "Context",
            "SubscribeJointState",
            "ArticulationController",
            "PublishJointState",
            "PublishClock",
        ]

        for node_name in required_nodes:
            node = og.Controller.node(f"/ActionGraph/{node_name}")
            if node is None:
                print(f"❌ Missing node: {node_name}")
                return False
            print(f"✅ Found node: {node_name}")

        print("\n✅ All required nodes present")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def delete_existing_graph():
    """Delete existing action graph if it exists."""
    try:
        graph = og.Controller.graph("/ActionGraph")
        if graph is not None:
            print("Deleting existing action graph...")
            omni.kit.commands.execute('DeletePrims', paths=['/ActionGraph'])
            print("✅ Deleted existing action graph")
            return True
    except Exception:
        pass  # Graph doesn't exist
    return False


def main():
    """Main setup function."""
    print("="*60)
    print("LeKiwi Isaac Sim Omnigraph Setup")
    print("="*60)
    print()

    # Option to delete existing graph
    delete_existing = input("Delete existing action graph? (y/N): ").strip().lower()
    if delete_existing == 'y':
        delete_existing_graph()

    # Create new graph
    success = create_ros2_action_graph()

    if success:
        # Verify setup
        verify_omnigraph_setup()

        print("\n" + "="*60)
        print("Setup complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Open Action Graph editor (Window → Visual Scripting → Action Graph)")
        print("2. Select ArticulationController node")
        print("3. In Property panel, set 'targetPrim' to /World/LeKiwi")
        print("4. Select PublishJointState node")
        print("5. In Property panel, set 'targetPrim' to /World/LeKiwi")
        print("6. Press Play to start simulation")
        print("\nROS2 Integration:")
        print("  - Ensure ROS_DOMAIN_ID=10 in your ROS2 environment")
        print("  - Topics will use RELIABLE QoS for joint_states")
        print("  - Use /joint_command to control robot")
        print("  - Monitor /joint_states for feedback")
        print("  - /clock provides simulation time")
    else:
        print("\n❌ Setup failed. Please check errors above.")


if __name__ == "__main__":
    main()
