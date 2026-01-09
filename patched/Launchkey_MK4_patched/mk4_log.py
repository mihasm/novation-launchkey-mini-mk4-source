# mk4_log.py
# Shared logger for Launchkey MK4 patched scripts

import logging
import os
import sys
import traceback

_LOGGER_NAME = "Launchkey_MK4"
_LOG_FILENAME = "launchkey_mk4.log"
LOGGING_ENABLED = True   # set to False to completely disable logging

def _create_logger():
    logger = logging.getLogger(_LOGGER_NAME)

    if not LOGGING_ENABLED:
        # Hard disable: no handlers, no propagation, no file creation
        logger.handlers.clear()
        logger.propagate = False
        logger.disabled = True
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # absolutely required in Ableton

    # Avoid duplicate handlers on script reload
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return logger

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, _LOG_FILENAME)

        fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        logger.debug("=== Logger initialized (%s) ===", log_path)

    except Exception:
        sh = logging.StreamHandler(stream=sys.stderr)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        logger.error(
            "Failed to initialize file logger:\n%s",
            traceback.format_exc(),
        )

    return logger


# Public accessor
def get_logger(name=None):
    """
    name: optional sub-logger name (e.g. 'session', 'mappings')
    """
    base = _create_logger()
    if name:
        return base.getChild(name)
    return base
