from setuptools import setup

package_name = "lekiwi_trajectory_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", ["config/trajectory_bridge.yaml"]),
        ("share/" + package_name + "/launch", ["lekiwi_trajectory_bridge/launch/trajectory_executor.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="vpraise",
    maintainer_email="vpraise@example.com",
    description="MoveIt FollowJointTrajectory executor for Isaac Sim",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "lekiwi_arm_trajectory_executor = lekiwi_trajectory_bridge.trajectory_executor_node:main",
        ],
    },
)
