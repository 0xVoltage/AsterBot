#!/usr/bin/env python3
"""
Setup script para AsterBot
"""

from setuptools import setup, find_packages
import os

# Ler README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Ler requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="asterbot",
    version="1.0.0",
    author="AsterBot Team",
    description="Bot de trading automatizado para Aster Dex Perpetuals",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "asterbot=asterbot.bot:main",
        ],
    },
    include_package_data=True,
    package_data={
        "asterbot": ["config/*.json"],
    },
)