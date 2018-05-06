#!/usr/bin/env python
# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""

try:
    from setuptools import setup
except ImportError:
    print("Please install the setuptools package")
    exit(1)

import os
import livechat


requirements_file = 'requirements.txt'
currentdir = os.path.dirname(__file__)
requires = os.path.join(currentdir, requirements_file)
requires = open(requires, 'r').read().splitlines()

setup(
    name='livechat',
    version=livechat.__version__,
    author=livechat.__author__,
    packages=['livechat'],
    author_email="ismaelrlgv@gmail.com",
    description="Video chat server",
    url="https://kwargs.net.ve",
    license='MIT',
    install_requires=requires,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        #"Programming Language :: Python :: 3",
        #"Programming Language :: Python :: 3.4",
        #"Programming Language :: Python :: 3.5",
    ],
    entry_points=dict(console_scripts=[
        'lc_server = livechat.server_cli:main',
        'lc_client = livechat.client_cli:main'
        ]
    )
)
