from setuptools import setup, find_packages

setup(

    name="Hava",
    version="0.0.1",
    author="Jakub Czaplicki",
    author_email="jakub.czaplicki@gmail.com",
    description="Yet another environmental data collectors",
    long_description='Hava - Environmental Data Collectors\n'
                     '==========================\n'
                     '\n'
                     'Contains: '
                     '* Air quality sensor data collector.',
    url="https://bitbucket.org/jakubczaplicki/hava",
    packages=find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    entry_points={
        'console_scripts': [
            'airquality_data_collector ='
            ' hava.airquality_data_collector.cli:main',
        ],
    },
    extras_require={'test': []},
    install_requires=[
        'pyserial==3.4',
        'aiosqlite'
    ],
)
