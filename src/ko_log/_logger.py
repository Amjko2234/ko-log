import inspect
import os
import sys
import threading
from _io import FileIO
from _thread import lock
from datetime import datetime, timezone
from inspect import Traceback
from pathlib import Path
from types import FrameType, ModuleType

from aiofiles.threadpool import binary

from .levels import LogLevel
from .types import Context, EventDict, ExcInfo, FileTextMode
from .utils import validate_file_path

# =====================================================================================
#   Internal logger of `LoggerFactory`
# =====================================================================================


class InternalLog:
    """Logs process of creating loggers from configurations."""

    def __init__(
        self,
        filename: str | Path,
        mode: FileTextMode,
        encoding: str,
    ) -> None:
        self._filepath: Path = validate_file_path(
            path=filename, create_missing_dir=True
        )
        self._file: binary.AsyncFileIO | None = None
        self._file_sync: FileIO | None = None
        self._mode: FileTextMode = mode
        self._encoding: str = encoding

        self._fmt: str = (
            "[%(asctime)s] [%(level)-8s] [%(lineno)-4s::%(funcName)s] %(event)s"
        )
        self._datefmt: str = "%Y-%m-%d %H:%M:%S"

        self._lock: lock = threading.Lock()

    # ---------------------------------------------------------------------------------
    #   Logging methods
    # ---------------------------------------------------------------------------------

    def debug(self, message: str, /, **context: Context) -> None:
        self.log(message, level=LogLevel.DEBUG, frame_count=2, **context)

    def info(self, message: str, /, **context: Context) -> None:
        self.log(message, level=LogLevel.INFO, frame_count=2, **context)

    def warning(self, message: str, /, **context: Context) -> None:
        self.log(message, level=LogLevel.WARNING, frame_count=2, **context)

    warn = warning

    def error(self, message: str, /, **context: Context) -> None:
        self.log(message, level=LogLevel.ERROR, frame_count=2, **context)

    def critical(self, message: str, /, **context: Context) -> None:
        self.log(message, level=LogLevel.CRITICAL, frame_count=2, **context)

    fatal = critical

    def log(
        self,
        message: str,
        /,
        level: LogLevel = LogLevel.NOTSET,
        frame_count: int = 1,
        **ctx: Context,
    ) -> None:
        frame: FrameType = sys._getframe(  # pyright: ignore[reportPrivateUsage]
            frame_count
        )
        event_dict: EventDict = {
            "event": message,
            "level": level.value,
            "exc_info": self._is_exception(level, **ctx),
            **self._extract_caller_info(frame),
            "context": {**ctx},
        }
        self._log(event_dict)

    def _log(self, event_dict: EventDict) -> None:
        date: datetime = event_dict.pop(  # pyright: ignore[reportAny]
            "timestamp", datetime.now(tz=timezone.utc)
        )
        event_dict["asctime"] = date.strftime(format=self._datefmt)
        event_dict["event"] = self._fmt % event_dict

        self._write(msg=event_dict["event"])

    # ---------------------------------------------------------------------------------
    #   Helper/Private methods
    # ---------------------------------------------------------------------------------

    def _extract_caller_info(self, frame: FrameType) -> dict[str, str]:
        frame_info: Traceback = inspect.getframeinfo(frame)
        module: ModuleType | None = inspect.getmodule(object=frame)

        return {
            "pathname": os.path.abspath(path=frame_info.filename),
            "filename": Path(frame_info.filename).name,
            "lineno": str(frame_info.lineno),
            "funcName": frame_info.function,
            "module": module.__name__ if module else "unknown",
        }

    def _is_exception(self, level: str, **kwargs: Context) -> ExcInfo | None:
        if level in ("ERROR", "CRITICAL"):
            return sys.exc_info()
        elif ("exc_info" not in kwargs) and (sys.exc_info()[0] is not None):
            return sys.exc_info()
        else:
            return None

    def _write(self, msg: str) -> None:
        line: str = msg + "\n"

        if self._file_sync is None:
            self._open_sync()
        assert self._file_sync is not None

        with self._lock:
            _ = self._file_sync.write(line.encode(encoding=self._encoding))
            self._file_sync.flush()

    def _open_sync(self) -> None:
        self._file_sync = self._filepath.open(
            self._mode,
            buffering=0,
        )
