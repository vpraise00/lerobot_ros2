from setuptools import setup

package_name = "lekiwi_base_control"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", ["config/kiwi_base_controller.yaml"]),
        ("share/" + package_name + "/launch", ["lekiwi_base_control/launch/kiwi_base_controller.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="vpraise",
    maintainer_email="vpraise@example.com",
    description="cmd_vel to wheel JointState publisher for LeKiwi.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "lekiwi_kiwi_base_controller = lekiwi_base_control.base_controller_node:main",
        ],
    },
)
