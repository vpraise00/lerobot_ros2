from setuptools import find_packages, setup

package_name = "lekiwi_isaac_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        ("share/{0}".format(package_name), ["package.xml"]),
        ("share/{0}/config".format(package_name), ["config/lekiwi_sim.yaml"]),
        ("share/{0}/launch".format(package_name), ["launch/lekiwi_isaac_bridge.launch.py"]),
        ("share/{0}".format(package_name), ["README.md", "README_OMNIGRAPH.md"]),
    ],
    install_requires=[
        "setuptools",
        "pyyaml",
    ],
    zip_safe=True,
    maintainer="unknown",
    maintainer_email="unknown@example.com",
    description="Bridge Float64MultiArray joint commands to JointState for LeKiwi in Isaac Sim.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["bridge_node = lekiwi_isaac_bridge.bridge_node:main"],
    },
)
