import setuptools


distribution_directory = '/usr/share/linux_thermaltake_rgb_plus'

setuptools.setup(
    name='thermaltake_rgb_plus',
    version='1.0',
    install_requires=[
            'numpy',
            'pyusb',
            'psutil',
            'pyyaml'
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            'thermaltake_rgb_plus=linux_thermaltake_rgb_plus.daemon.main:main',
        ],
    },
    data_files=[
        (distribution_directory,
            ['linux_thermaltake_rgb_plus/assets/linux_thermaltake_rgb_plus.service']),
        (distribution_directory, ['linux_thermaltake_rgb_plus/assets/config.yml'])]
)

