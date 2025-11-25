import os
from pathlib import Path

from setuptools import find_packages, setup

package_name = "lekiwi_description"

package_dir = Path(__file__).resolve().parent
repo_root = package_dir.parents[2]
canonical_urdf_dir = repo_root / "urdf" / "lekiwi"


def package_directory(src_dir: Path, dest_subdir: str):
    entries = []
    if not src_dir.exists():
        return entries
    for root, _, files in os.walk(src_dir):
        if not files:
            continue
        root_path = Path(root)
        rel = root_path.relative_to(src_dir)
        dest = Path("share") / package_name / dest_subdir
        if rel != Path("."):
            dest /= rel
        entries.append((str(dest), [str(root_path / f) for f in files]))
    return entries


urdf_data_files = package_directory(canonical_urdf_dir, "urdf")

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/srdf", ["srdf/lekiwi.srdf"]),
        (
            "share/" + package_name + "/config",
            [
                "config/ros2_control.yaml",
                "config/kinematics.yaml",
                "config/trajectory_execution.yaml",
                "config/joint_limits.yaml",
                "config/pilz_cartesian_limits.yaml",
            ],
        ),
    ]
    + urdf_data_files,
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="todo@example.com",
    description="Robot description for LeKiwi",
    license="Apache-2.0",
    entry_points={},
)
