"""
Version utilities for Open Notebook.
Handles version comparison and package version lookup.
"""

from importlib.metadata import PackageNotFoundError, version

from packaging.version import parse as parse_version


def get_installed_version(package_name: str) -> str:
    """
    Get the version of an installed package.

    Args:
        package_name (str): Name of the installed package

    Returns:
        str: Version string of the installed package

    Raises:
        PackageNotFoundError: If the package is not installed
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        raise PackageNotFoundError(f"Package '{package_name}' not found")


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic versions.

    Args:
        version1 (str): First version string
        version2 (str): Second version string

    Returns:
        int: -1 if version1 < version2
              0 if version1 == version2
              1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0
