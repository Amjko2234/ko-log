from __future__ import annotations

import enum
from typing import TypeAlias


class LogLevel(enum.StrEnum):
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    WARN = WARNING
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = CRITICAL


class _LogLevel(enum.IntEnum):
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    WARN = WARNING
    FATAL = CRITICAL


LogLevels: TypeAlias = int | str | LogLevel

NAME_TO_LEVEL: dict[str, int] = {L: _LogLevel[L].value for L in LogLevel.__members__}
LEVEL_TO_NAME: dict[int, str] = {L.value: L.name for L in _LogLevel}


def get_level_name(level: LogLevels) -> str:
    try:
        if isinstance(level, str):
            lvl: int = NAME_TO_LEVEL[level]
        elif isinstance(level, LogLevel):
            lvl = NAME_TO_LEVEL[level.value]
        else:
            lvl = level
        return LEVEL_TO_NAME[lvl]
    except KeyError as exc:
        raise ValueError(f"Unkown level name: {level}") from exc


def check_level(level: LogLevels) -> int:
    if isinstance(level, int):
        if level not in LEVEL_TO_NAME:
            raise ValueError(f"Unknown level: {level}")
        return level
    else:
        try:
            return NAME_TO_LEVEL[str(level)]
        except KeyError:
            raise ValueError(f"Unknown level: {level}")
