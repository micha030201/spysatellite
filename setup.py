from setuptools import setup

setup(
    name='spysatellite',
    packages=['spysatellite'],
    include_package_data=True,
    install_requires=[
        'flask',
        'beautifulsoup4',
        'requests',
        'html5lib',
    ],
)
