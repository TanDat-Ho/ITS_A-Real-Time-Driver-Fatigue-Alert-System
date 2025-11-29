"""
Driver Fatigue Alert System

A real-time computer vision system for detecting driver fatigue using
MediaPipe face detection and analysis algorithms.

Author: ITS Project Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "ITS Project Team" 
__email__ = "contact@its-project.com"
__license__ = "MIT"
__description__ = "Real-time Driver Fatigue Alert System using computer vision"

# Package metadata for PyInstaller and setuptools
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    "__description__"
]

# Version info tuple for programmatic access
VERSION_INFO = tuple(map(int, __version__.split('.')))

def get_version():
    """Get version string."""
    return __version__

def get_package_info():
    """Get complete package information."""
    return {
        'name': 'driver-fatigue-alert-system',
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__,
        'description': __description__,
        'version_info': VERSION_INFO
    }