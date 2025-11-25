from setuptools import setup

package_name = "lekiwi_perception"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", ["config/camera_bridge.yaml"]),
        ("share/" + package_name + "/launch", ["lekiwi_perception/launch/lekiwi_vslam_nav.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="vpraise",
    maintainer_email="vpraise@example.com",
    description="Camera perception helpers for LeKiwi Isaac Sim integration.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "camera_bridge_node = lekiwi_perception.camera_bridge_node:main",
        ],
    },
)
