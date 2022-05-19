from setuptools import find_packages, setup

setup(
    name='kube-manifest-cleaner',
    packages=find_packages(),
    entry_points={'console_scripts': [
        'kube-manifest-cleaner = manifest_cleaner.__main__:main',
    ]},
    install_requires=['ruamel.yaml'],
)
