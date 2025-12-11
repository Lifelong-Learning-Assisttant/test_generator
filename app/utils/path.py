"""
Path utilities for sandboxed file access.
"""
from pathlib import Path


def safe_join(base_dir: Path, name: str) -> Path:
    """
    Safely join a filename to a base directory, preventing traversal.

    Args:
        base_dir: Base directory
        name: Requested filename (may include unsafe components)

    Returns:
        Resolved path within base_dir

    Raises:
        ValueError: If resolution escapes the base directory
    """
    base_dir = base_dir.resolve()
    safe_name = Path(name).name
    candidate = (base_dir / safe_name).resolve()

    if not str(candidate).startswith(str(base_dir)):
        raise ValueError("Invalid path")

    return candidate
