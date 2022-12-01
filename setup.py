#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

import xarray_video

requirements = ["xarray", "numcodecs", "av"]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest",
]

setup(
    author="Oceanum Developers",
    author_email="developers@oceanum.science",
    description="Xarray accessor and zarr codec for storing and accessing time and/or space stacked video",
    entry_points={
        "console_scripts": [
            "oceanum=oceanum.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="oceanum,video,xarray",
    documentation="https://xarray-video.readthedocs.io",
    name="xarray-video",
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/oceanum/xarray-video",
    version=xarray_video.__version__,
    zip_safe=False,
)
