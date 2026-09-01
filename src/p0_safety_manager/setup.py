from setuptools import find_packages, setup

package_name = "p0_safety_manager"

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
    description="Project0 fail-safe motion command arbiter.",
    license="Proprietary",
    entry_points={"console_scripts": ["command_arbiter = p0_safety_manager.node:main"]},
)
