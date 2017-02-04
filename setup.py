from setuptools import setup

setup(
    name='spysatellite',
    url='https://github.com/micha030201/spysatellite',
    packages=['spysatellite'],
    include_package_data=True,
    install_requires=[
        'flask',
        'beautifulsoup4',
        'requests',
        'lxml',
    ],
)
