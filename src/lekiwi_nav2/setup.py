from setuptools import find_packages, setup

package_name = "lekiwi_nav2"

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
                "lekiwi_nav2/launch/nav2.launch.py",
                "lekiwi_nav2/launch/lekiwi_nav2_with_kiwi.launch.py",
            ],
        ),
        ("share/" + package_name + "/config", ["config/nav2_params.yaml", "config/slam_params.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="todo@example.com",
    description="Nav2 configuration for LeKiwi",
    license="Apache-2.0",
    entry_points={},
)
