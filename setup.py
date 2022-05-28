from setuptools import find_packages, setup

setup(
    name='kube-manifest-processor',
    packages=find_packages(),
    entry_points={'console_scripts': [
        'kube-manifest-processor = kube_manifest_processor.__main__:main',
    ]},
    install_requires=[
        'ruamel.yaml',
        'requests',
    ],
)
