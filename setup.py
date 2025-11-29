#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Driver Fatigue Alert System
Created for PyInstaller packaging and distribution

Author: Dat
Version: 1.0.0
License: MIT
"""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# Get the directory containing this file
HERE = Path(__file__).parent.absolute()

# Read the README file for long description
try:
    with open(HERE / "README.md", "r", encoding="utf-8") as readme_file:
        long_description = readme_file.read()
except FileNotFoundError:
    long_description = "Real-time Driver Fatigue Alert System using computer vision and MediaPipe"

# Read requirements from requirements.txt
def read_requirements(filename):
    """Read requirements from requirements file"""
    try:
        with open(HERE / filename, "r", encoding="utf-8") as req_file:
            return [
                line.strip() 
                for line in req_file 
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using minimal requirements.")
        return []

# Get version from package __init__.py or fallback
def get_version():
    """Get version from package or return default"""
    try:
        version_file = HERE / "src" / "__init__.py"
        if version_file.exists():
            with open(version_file, "r") as f:
                for line in f:
                    if line.startswith("__version__"):
                        return line.split("=")[1].strip().strip("\"'")
    except Exception:
        pass
    return "1.0.0"

# Package requirements
install_requires = read_requirements("requirements.txt")
build_requires = read_requirements("requirements-build.txt")

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
    "pre-commit>=2.20.0"
]

# Data files and assets
def get_data_files():
    """Get all data files for packaging"""
    data_files = []
    
    # Assets directory
    assets_dir = HERE / "assets"
    if assets_dir.exists():
        for root, dirs, files in os.walk(assets_dir):
            if files:
                relative_root = os.path.relpath(root, HERE)
                data_files.append((
                    relative_root,
                    [os.path.join(root, file) for file in files]
                ))
    
    # Config files
    config_dir = HERE / "config"
    if config_dir.exists():
        for root, dirs, files in os.walk(config_dir):
            if files:
                relative_root = os.path.relpath(root, HERE)
                data_files.append((
                    relative_root,
                    [os.path.join(root, file) for file in files]
                ))
    
    # Documentation
    docs_files = ["README.md", "LICENSE", "CHANGELOG.md"]
    existing_docs = [f for f in docs_files if (HERE / f).exists()]
    if existing_docs:
        data_files.append((".", existing_docs))
    
    return data_files

# Package configuration
setup(
    # Basic package info
    name="driver-fatigue-alert-system",
    version=get_version(),
    description="Real-time Driver Fatigue Alert System using computer vision and MediaPipe",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Author info
    author="Dat",
    author_email="dat@example.com",
    url="https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System",
    
    # License
    license="MIT",
    
    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=install_requires,
    extras_require={
        "dev": dev_requirements,
        "build": build_requires,
        "all": dev_requirements + build_requires
    },
    
    # Data files
    include_package_data=True,
    package_data={
        "": [
            "*.json",
            "*.yaml", 
            "*.yml",
            "*.png",
            "*.jpg",
            "*.wav",
            "*.mp3",
            "*.ico",
            "*.icns"
        ]
    },
    data_files=get_data_files(),
    
    # Entry points for command-line interface
    entry_points={
        "console_scripts": [
            "fatigue-detection=launcher:main",
            "fatigue-gui=launcher:main",
            "fatigue-cli=launcher:cli_main",
        ]
    },
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X"
    ],
    
    # Keywords
    keywords=[
        "computer-vision", 
        "fatigue-detection", 
        "driver-monitoring",
        "mediapipe",
        "opencv", 
        "real-time",
        "safety",
        "ai",
        "machine-learning"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System/issues",
        "Source": "https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System",
        "Documentation": "https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System/tree/main/docs"
    },
    
    # Zip safe
    zip_safe=False,
)

# Post-installation message
print("\n" + "="*60)
print("🚀 Driver Fatigue Alert System Setup Complete!")
print("="*60)
print("📦 Package: driver-fatigue-alert-system")
print(f"📋 Version: {get_version()}")
print("🐍 Python: >= 3.8")
print("\n💡 Quick Start:")
print("   python launcher.py              # GUI mode")
print("   python launcher.py --cli        # CLI mode")
print("   python launcher.py --help       # Show help")
print("\n🔧 Build executable:")
print("   # Windows")
print("   .\\build-windows.ps1")
print("   # Linux")  
print("   ./build-linux.sh")
print("   # macOS")
print("   ./build-macos.sh")
print("="*60)
