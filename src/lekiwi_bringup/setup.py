from setuptools import find_packages, setup

package_name = "lekiwi_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", [
            "lekiwi_bringup/launch/lekiwi_sim_bringup.launch.py",
            "lekiwi_bringup/launch/lekiwi_core.launch.py",
            "lekiwi_bringup/launch/lekiwi_nav2.launch.py",
            "lekiwi_bringup/launch/lekiwi_moveit2.launch.py",
            "lekiwi_bringup/launch/lekiwi_mobile_manip.launch.py",
        ]),
        ("share/" + package_name + "/config", [
            "config/ros2_controllers.yaml",
            "config/joint_names.yaml",
        ]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="todo@example.com",
    description="Bringup launch files for LeKiwi",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [],
    },
)
