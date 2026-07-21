"""
Logging setup for aegisScout.

LOGS_DIR resolution (mirrors toml_config.py):

  1. ``$AEGISSCout_LOGS_DIR`` (env override; tests use this)
  2. ``sys._MEIPASS / "logs"``  (frozen / PyInstaller)
  3. Walk up from ``Path(__file__).parent`` to find a ``logs/`` dir
     (covers the dev layout: ``.../project_root/logs/``)
  4. ``Path.cwd() / "logs"``     (last-resort fallback)

The directory is created on import. Public symbols expose the
resolved path so tests and CLI can override / inspect.
"""
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _resolve_logs_dir() -> Path:
    """Return the most likely on-disk logs directory."""
    env_dir = os.environ.get("AEGISSCout_LOGS_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        return p  # we will create it below if needed

    # Frozen (PyInstaller): the logs dir should be next to the executable
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "logs"

    # Dev: walk up parents to find a ``logs/`` dir.
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "logs"
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Last-resort fallback (CWD).
    return Path.cwd() / "logs"


LOGS_DIR: Path = _resolve_logs_dir()
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _set_logs_dir(path: Path) -> None:
    """Override the resolved logs dir (used by tests)."""
    global LOGS_DIR
    LOGS_DIR = Path(path)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Formatter + handlers
# ---------------------------------------------------------------------------

# Determine default log level from environment or default to DEBUG/INFO
_env_level = os.environ.get("AEGISSCout_LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_LEVEL = getattr(logging, _env_level, logging.INFO)

# Maximum detail formatter including timestamp with milliseconds, Level, Thread, Module:Line, and Message
detailed_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d [%(levelname)s] [%(threadName)s] [%(filename)s:%(lineno)d] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def create_rotating_handler(filename: str, level: int) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        LOGS_DIR / filename,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    handler.setFormatter(detailed_formatter)
    handler.setLevel(level)
    return handler


# Rotating file handlers
main_handler = create_rotating_handler("aegisScout.log", logging.DEBUG)
discovery_handler = create_rotating_handler("discovery.log", logging.DEBUG)
outreach_handler = create_rotating_handler("outreach.log", logging.DEBUG)
errors_handler = create_rotating_handler("errors.log", logging.WARNING)

# Console Handler (to display errors/warnings/info on CLI with maximum detail)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(detailed_formatter)
console_handler.setLevel(DEFAULT_LOG_LEVEL)


# Logger namespace routing filter
class NameFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record):
        return record.name.startswith(self.prefix)


# Route specific logger messages to their dedicated files
discovery_handler.addFilter(NameFilter("aegisScout.discovery"))
outreach_handler.addFilter(NameFilter("aegisScout.outreach"))


# ---------------------------------------------------------------------------
# Session Log Handler (Markdown and JSON lines)
# ---------------------------------------------------------------------------
import json
import threading
from datetime import datetime

class SessionLogHandler(logging.Handler):
    """
    Custom handler to log the current execution session to Markdown and JSON Lines.
    Uses an in-memory buffer and background thread flusher for optimal disk I/O performance.
    """
    def __init__(self, logs_dir: Path, flush_interval: float = 2.0):
        super().__init__()
        self.sessions_dir = logs_dir / "sessions"
        self._buffer_lock = threading.Lock()
        self._buffer: list[dict] = []
        self._flush_interval = flush_interval
        self._timer: Optional[threading.Timer] = None
        self._stopped = False
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
            # Create a unique session timestamp
            self.session_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.md_file_path = self.sessions_dir / f"session_{self.session_time_str}.md"
            self.json_file_path = self.sessions_dir / f"session_{self.session_time_str}.json"
            
            # Write markdown header
            with open(self.md_file_path, "w", encoding="utf-8") as f:
                f.write(f"# aegisScout Session Log — {self.session_time_str.replace('_', ' ')}\n\n")
                f.write(f"- **Start Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **Python Version**: {sys.version.split()[0]}\n\n")
                f.write("## Log Entries\n\n")
            self._initialized = True
            self._schedule_flush()
        except Exception as e:
            self._initialized = False
            sys.stderr.write(f"Failed to initialize SessionLogHandler: {e}\n")

    def _schedule_flush(self):
        if self._stopped:
            return
        self._timer = threading.Timer(self._flush_interval, self.flush)
        self._timer.daemon = True
        self._timer.start()

    def emit(self, record):
        if not self._initialized:
            return
        try:
            time_str = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "timestamp": time_str,
                "level": record.levelname,
                "thread": record.threadName,
                "logger": record.name,
                "message": record.getMessage()
            }
            with self._buffer_lock:
                self._buffer.append(entry)
        except Exception:
            self.handleError(record)

    def flush(self):
        if not self._initialized:
            return
        with self._buffer_lock:
            if not self._buffer:
                if not self._stopped:
                    self._schedule_flush()
                return
            to_write = list(self._buffer)
            self._buffer.clear()

        try:
            md_lines = []
            json_lines = []
            for item in to_write:
                md_lines.append(f"* **{item['timestamp']}** `[{item['level']}]` `[{item['thread']}]` `{item['logger']}` — {item['message']}\n")
                json_lines.append(json.dumps(item, ensure_ascii=False) + "\n")

            with open(self.md_file_path, "a", encoding="utf-8") as f:
                f.writelines(md_lines)

            with open(self.json_file_path, "a", encoding="utf-8") as f:
                f.writelines(json_lines)
        except Exception:
            pass
        finally:
            if not self._stopped:
                self._schedule_flush()

    def close(self):
        self._stopped = True
        if self._timer:
            self._timer.cancel()
        self.flush()
        super().close()


# Initialize session handler
session_handler = SessionLogHandler(LOGS_DIR)

# Main Logger Setup
root_logger = logging.getLogger("aegisScout")
root_logger.setLevel(logging.INFO)

# Attach all handlers (filtering logic is managed inside handlers)
root_logger.addHandler(main_handler)
root_logger.addHandler(discovery_handler)
root_logger.addHandler(outreach_handler)
root_logger.addHandler(errors_handler)
root_logger.addHandler(console_handler)
root_logger.addHandler(session_handler)


import time
from contextlib import contextmanager

@contextmanager
def log_execution_time(logger: logging.Logger, task_name: str):
    """Context manager to measure and log execution time of code blocks."""
    start_time = time.perf_counter()
    logger.debug(f"Starting execution: '{task_name}'...")
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(f"Completed execution: '{task_name}' in {elapsed:.2f}ms")


def get_logger(name: str):
    """
    Returns a logger prefixed with aegisScout.
    E.g. get_logger("discovery.osm") -> logger named 'aegisScout.discovery.osm'
    """
    logger = logging.getLogger(f"aegisScout.{name}")
    logger.setLevel(DEFAULT_LOG_LEVEL)
    return logger
