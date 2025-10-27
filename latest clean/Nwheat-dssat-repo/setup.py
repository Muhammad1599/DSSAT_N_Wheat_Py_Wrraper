#!/usr/bin/env python3
"""
Setup script for NWheat DSSAT Experiment package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="nwheat-dssat-experiment",
    version="1.0.0",
    author="Research Team",
    author_email="research@university.edu",
    description="Complete NWheat DSSAT experimental setup with validation data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/NWheat-DSSAT-Experiment",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/NWheat-DSSAT-Experiment/issues",
        "Source": "https://github.com/yourusername/NWheat-DSSAT-Experiment",
        "Documentation": "https://github.com/yourusername/NWheat-DSSAT-Experiment/docs",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": ["pytest>=6.0", "pytest-cov>=2.12", "black>=21.0", "flake8>=3.9"],
        "docs": ["sphinx>=4.0", "sphinx-rtd-theme>=0.5"],
        "jupyter": ["jupyter>=1.0", "ipykernel>=6.0"],
    },
    entry_points={
        "console_scripts": [
            "nwheat-run=nwheat_runner.runner:main",
            "nwheat-analyze=nwheat_runner.analyzer:main",
            "nwheat-validate=nwheat_runner.validator:main",
        ],
    },
    include_package_data=True,
    keywords="wheat, dssat, nwheat, crop modeling, agriculture, simulation, validation",
    zip_safe=False,
)
