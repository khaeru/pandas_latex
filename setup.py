#!/usr/bin/env python
# encoding: utf-8
from setuptools import find_packages, setup

setup(
    name='pandas_latex',
    version='0.1.dev0',
    license='GNU GPL v3',
    author='Paul Natsuo Kishimoto',
    author_email='mail@paul.kishimoto.name',
    url='https://github.com/khaeru/pandas_latex',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    setup_requires=['pytest-runner'],
    extras_require={
        'test': ['pandas', 'pytest', 'pytest-cov'],
        },
    )
