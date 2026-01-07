from __future__ import annotations

import logging
import os
import sys
import traceback

import Live

from ableton.v3.base import listens, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import SendValueInputControl


# --------------------------------------------------------------------------------------
# Per-script logger (single file next to this script)
# --------------------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_PATH = os.path.join(_SCRIPT_DIR, "launchkey_mk4_scale.log")

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.propagate = False

if not any(isinstance(h, logging.FileHandler) for h in _logger.handlers):
    try:
        fh = logging.FileHandler(_LOG_PATH, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        _logger.addHandler(fh)
        _logger.debug("Logger initialized. Log path: %s", _LOG_PATH)
    except Exception:
        sh = logging.StreamHandler(stream=sys.stderr)
        sh.setLevel(logging.DEBUG)
        _logger.addHandler(sh)
        _logger.error("Failed to initialize file logger:\n%s", traceback.format_exc())


FIRMWARE_SCALES = (
    (0, 2, 4, 5, 7, 9, 11),
    (0, 2, 3, 5, 7, 8, 10),
    (0, 2, 3, 5, 7, 9, 10),
    (0, 2, 4, 5, 7, 9, 10),
    (0, 2, 4, 6, 7, 9, 11),
    (0, 1, 3, 5, 7, 8, 10),
    (0, 1, 3, 5, 6, 8, 10),
    (0, 2, 4, 6, 8, 10),
    (0, 1, 3, 4, 6, 7, 9, 10),
    (0, 2, 3, 5, 6, 8, 9, 11),
    (0, 3, 5, 6, 7, 10),
    (0, 3, 5, 7, 10),
    (0, 2, 4, 7, 9),
    (0, 2, 3, 5, 7, 8, 11),
    (0, 2, 4, 5, 7, 8, 11),
    (0, 2, 3, 6, 7, 9, 10),
    (0, 1, 4, 5, 7, 8, 10),
    (0, 2, 3, 5, 7, 9, 11),
    (0, 2, 4, 6, 8, 9, 11),
    (0, 2, 4, 6, 7, 9, 10),
    (0, 1, 3, 4, 6, 8, 10),
    (0, 1, 3, 4, 5, 6, 8, 10),
    (0, 1, 4, 5, 7, 8, 11),
    (0, 2, 3, 6, 7, 8, 11),
    (0, 2, 3, 7, 8),
    (0, 1, 5, 7, 10),
    (0, 1, 5, 6, 10),
    (0, 2, 3, 7, 9),
    (0, 1, 3, 7, 8),
    (0, 1, 5, 7, 8),
)

_logger.debug("Building SCALE_NAMES from Live.Song.get_all_scales_ordered()")
try:
    _all_scales = Live.Song.get_all_scales_ordered()
    _logger.debug("Live.Song.get_all_scales_ordered() returned %d items", len(_all_scales))
    _intervals_to_name = {s[1]: s[0] for s in _all_scales}
    SCALE_NAMES = [None] + [_intervals_to_name.get(intervals, None) for intervals in FIRMWARE_SCALES]
    _logger.debug("SCALE_NAMES built (len=%d)", len(SCALE_NAMES))
except Exception:
    _logger.exception("Exception building SCALE_NAMES")
    # Fail-safe: keep a minimal list so script can load and you can see the error.
    SCALE_NAMES = [None]
del FIRMWARE_SCALES


class ScaleComponent(Component):
    scale_type_control = SendValueInputControl()
    root_note_control = SendValueInputControl()

    def __init__(self, *a, **k):
        _logger.debug("ENTER ScaleComponent.__init__(a=%r, k=%r)", a, k)
        try:
            super().__init__(*a, name="Scales", **k)
            _logger.debug("super().__init__ completed; self.song=%r", getattr(self, "song", None))

            def make_task(fn):
                _logger.debug("ENTER make_task(fn=%r)", fn)
                try:
                    t = self._tasks.add(task.sequence(task.wait(0.1), task.run(fn)))
                    _logger.debug("Task created: %r; killing initially", t)
                    t.kill()
                    return t
                except Exception:
                    _logger.exception("Exception in ScaleComponent.__init__.make_task")
                    raise

            _logger.debug("Creating _update_scale_type_control_task")
            self._update_scale_type_control_task = make_task(self._update_scale_type_control)

            _logger.debug("Creating _update_root_note_control_task")
            self._update_root_note_control_task = make_task(self._update_root_note_control)

            _logger.debug("Binding listeners to song")
            self.__on_scale_type_changed_in_song.subject = self.song
            self.__on_root_note_changed_in_song.subject = self.song

            _logger.debug("Priming listeners by calling them once")
            self.__on_scale_type_changed_in_song()
            self.__on_root_note_changed_in_song()

            _logger.debug("ScaleComponent.__init__ completed")
        except Exception:
            _logger.exception("Exception in ScaleComponent.__init__")
            raise

    @scale_type_control.value
    def scale_type_control(self, value, _):
        _logger.debug("ENTER ScaleComponent.scale_type_control(value=%r)", value)
        try:
            _logger.debug("Checking value in range(len(SCALE_NAMES)) (len=%d)", len(SCALE_NAMES))
            if value in range(len(SCALE_NAMES)):
                scale_name = SCALE_NAMES[value]
                _logger.debug("Resolved scale_name=%r for index=%r", scale_name, value)
                if scale_name is None:
                    _logger.debug("scale_name is None -> return")
                    return
                current = getattr(self.song, "scale_name", None)
                _logger.debug("Current song.scale_name=%r", current)
                if current != scale_name:
                    _logger.debug("Setting song.scale_name=%r", scale_name)
                    self.song.scale_name = scale_name
            else:
                _logger.debug("value out of range -> ignoring")
        except Exception:
            _logger.exception("Exception in ScaleComponent.scale_type_control handler")
            raise

    @root_note_control.value
    def root_note_control(self, value, _):
        _logger.debug("ENTER ScaleComponent.root_note_control(value=%r)", value)
        try:
            if value in range(12):
                current = getattr(self.song, "root_note", None)
                _logger.debug("Current song.root_note=%r", current)
                if current != value:
                    _logger.debug("Setting song.root_note=%r", value)
                    self.song.root_note = value
            else:
                _logger.debug("value out of 0..11 range -> ignoring")
        except Exception:
            _logger.exception("Exception in ScaleComponent.root_note_control handler")
            raise

    def _update_scale_type_control(self):
        _logger.debug("ENTER ScaleComponent._update_scale_type_control()")
        try:
            song_scale = getattr(self.song, "scale_name", None)
            _logger.debug("song.scale_name=%r; checking membership in SCALE_NAMES", song_scale)
            if song_scale in SCALE_NAMES:
                idx = SCALE_NAMES.index(song_scale)
                _logger.debug("Setting scale_type_control.value=%r", idx)
                self.scale_type_control.value = idx
            else:
                _logger.debug("song.scale_name not found in SCALE_NAMES -> no update")
        except Exception:
            _logger.exception("Exception in ScaleComponent._update_scale_type_control")
            raise

    def _update_root_note_control(self):
        _logger.debug("ENTER ScaleComponent._update_root_note_control()")
        try:
            rn = getattr(self.song, "root_note", None)
            _logger.debug("Setting root_note_control.value=%r", rn)
            self.root_note_control.value = rn
        except Exception:
            _logger.exception("Exception in ScaleComponent._update_root_note_control")
            raise

    @listens("scale_name")
    def __on_scale_type_changed_in_song(self):
        _logger.debug("ENTER ScaleComponent.__on_scale_type_changed_in_song() -> restart task")
        try:
            self._update_scale_type_control_task.restart()
            _logger.debug("_update_scale_type_control_task restarted")
        except Exception:
            _logger.exception("Exception in ScaleComponent.__on_scale_type_changed_in_song")
            raise

    @listens("root_note")
    def __on_root_note_changed_in_song(self):
        _logger.debug("ENTER ScaleComponent.__on_root_note_changed_in_song() -> restart task")
        try:
            self._update_root_note_control_task.restart()
            _logger.debug("_update_root_note_control_task restarted")
        except Exception:
            _logger.exception("Exception in ScaleComponent.__on_root_note_changed_in_song")
            raise
