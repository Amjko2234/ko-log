import os
from pathlib import Path
from typing import Literal, TypeAlias, overload

Encoding: TypeAlias = Literal["utf-8"]
ReadMode: TypeAlias = Literal["r", "rb"]


@overload
def read(path: Path, mode: Literal["rb"]) -> bytes: ...
@overload
def read(path: Path, mode: Literal["r"]) -> str: ...
def read(
    path: Path,
    mode: ReadMode = "r",
    *,
    encoding: Encoding = "utf-8",
    secured: bool = False,
) -> str | bytes:
    """
    Read contents of a file.

    (Taken from a local repository of Amjko's useful utils :>)
    """

    if secured:
        path = validate_file_path(
            path,
            must_exist=True,
            allow_creation=False,
        )
        with open(file=path, mode=mode, encoding=encoding) as file:
            return file.read()  # pyright: ignore[reportAny]

    # Assumes absolute path is validated
    if path.exists():
        with open(file=path, mode=mode, encoding=encoding) as file:
            return file.read()  # pyright: ignore[reportAny]
    return ""


def validate_file_path(
    path: Path | str,
    *,
    must_exist: bool = False,
    create_missing_dir: bool = False,
    allow_creation: bool = True,
    resolve_symlinks: bool = True,
) -> Path:
    """
    Validates, normalizes, and return a file path.

    (Taken from a local repository of Amjko's useful utils :>)
    """

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


def count_files_in_directory(dir: Path, pattern: str = "*.log*", /) -> int:
    """Count the number of log files in the directory."""

    return len(list[Path](dir.glob(pattern)))


def get_file_bsizes(files: list[Path], /) -> list[int]:
    """Get byte sizes of each file in sequence."""

    # Byte size
    return [file.stat().st_size for file in files if file.exists()]


def read_file_content(file: Path, /) -> str:
    """Basicly read file content and return its string output."""

    return read(path=file, mode="r")


def create_test_messages(count: int, msg_length: int = 10) -> list[str]:
    """Generate `msg_length` amount of characters, repeat for `count` lines."""

    # Width needed for the index (e.g., 2 for 0-99, 3 for 100-999, etc.)
    index_width: int = len(str(count - 1))
    # Reserve space for index and newline
    base_len: int = msg_length - index_width - 1
    if base_len < 0:
        raise ValueError("`msg_length` too small for index and newline")
    base_msg: str = "X" * base_len
    return [f"{base_msg}{i:0{index_width}d}\n" for i in range(count)]


def convert_to_byte(string: str, encoding: str = "utf-8", /) -> bytes:
    return string.encode(encoding)


def convert_from_byte(object: bytes, encoding: str = "utf-8", /) -> str:
    return object.decode(encoding)
