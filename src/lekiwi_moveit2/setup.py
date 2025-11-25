from setuptools import find_packages, setup

package_name = "lekiwi_moveit2"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            [
                "lekiwi_moveit2/launch/moveit.launch.py",
                "lekiwi_moveit2/launch/moveit_with_executor.launch.py",
                "lekiwi_moveit2/launch/rviz_only.launch.py",
            ],
        ),
        (
            "share/" + package_name + "/config",
            [
                "config/controllers.yaml",
                "config/kinematics.yaml",
                "config/moveit.rviz",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="todo@example.com",
    description="MoveIt2 configuration for LeKiwi",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "planning_scene_qos_bridge = lekiwi_moveit2.planning_scene_qos_bridge:main",
        ],
    },
)
