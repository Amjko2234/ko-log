import os
from pathlib import Path


def validate_file_path(
    path: Path | str,
    *,
    must_exist: bool = False,
    create_missing_dir: bool = False,
    allow_creation: bool = True,
    resolve_symlinks: bool = True,
) -> Path:
    """Validates, normalizes, and return a file path."""

    # Expand ~ (home) and env variables
    # `os.path.expanduser()` e.g., ~ -> /home/
    # `os.path.expandvars()` e.g., $HOME -> /home/
    path_: Path = Path(os.path.expandvars(os.path.expanduser(str(path))))

    # Convert relative to absolute
    # Resolve symlinks if necessary, don't worry about missing files
    path_ = path_.resolve(strict=False) if resolve_symlinks else path_.absolute()

    # Ensure parent dir exists (or create)
    if not path_.parent.exists():
        if create_missing_dir:
            path_.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(
                f"Path `{str(path_)}` does not exist, " + "enable `create_missing_dir`"
            )

    # Check file existence rules
    if must_exist and not path_.exists():
        raise FileNotFoundError(
            f"Path `{str(path)}` does not exist, enable `create_missing_dir`"
        )
    if not allow_creation and not path_.exists():
        raise FileNotFoundError(
            f"Path `{str(path)}` can not be created, enable `allow_creation`"
        )
    return path_
