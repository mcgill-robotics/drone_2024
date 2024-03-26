from setuptools import find_packages, setup

package_name = 'px4_offboard_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Imad',
    maintainer_email='imad.issafras@mail.mcgill.ca',
    description='Basic px4 offboard control',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'offboard_node = px4_offboard_control.offboard_node:main',
        ],
    },
)
