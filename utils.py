from pathlib import Path

def ensure_dir(path: str | Path) -> Path:
    """Ensure that a directory exists. If it does not, create it."""
    path = Path(path)
    path.mkdir(exist_ok=True)
    return path

def wipe_dir_files_only(root_dir):
    """Wipe a directory of all files."""
    root = Path(root_dir)
    for path in root.rglob("*"):
        if path.is_file():
            path.unlink()