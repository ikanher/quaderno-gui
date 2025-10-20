#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="quaderno_gui",
    version="0.1.2",
    description="A GUI application for managing DigitalPaper devices and Zotero integration.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "dpt-rp1-py",
    ],
    entry_points={"console_scripts": ["quaderno-gui = quaderno_gui.main:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
