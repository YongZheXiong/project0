from setuptools import find_packages, setup

package_name = "p0_base_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=("test",)),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Project0 maintainer",
    maintainer_email="maintainer@example.com",
    description="Fail-safe ROS 2 bridge for the Project0 H60 binary protocol.",
    license="Proprietary",
    entry_points={"console_scripts": ["base_bridge = p0_base_bridge.node:main"]},
)
