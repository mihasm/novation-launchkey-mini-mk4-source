from __future__ import annotations

import logging
import os
import sys
import traceback

import Live

from ableton.v3.base import listens, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import SendValueInputControl


from .mk4_log import get_logger
_logger = get_logger("scale")

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

try:
    _all_scales = Live.Song.get_all_scales_ordered()
    _intervals_to_name = {s[1]: s[0] for s in _all_scales}
    SCALE_NAMES = [None] + [_intervals_to_name.get(intervals, None) for intervals in FIRMWARE_SCALES]
except Exception:
    _logger.exception("Exception building SCALE_NAMES")
    # Fail-safe: keep a minimal list so script can load and you can see the error.
    SCALE_NAMES = [None]
del FIRMWARE_SCALES


class ScaleComponent(Component):
    scale_type_control = SendValueInputControl()
    root_note_control = SendValueInputControl()

    def __init__(self, *a, **k):
        try:
            super().__init__(*a, name="Scales", **k)

            def make_task(fn):
                try:
                    t = self._tasks.add(task.sequence(task.wait(0.1), task.run(fn)))
                    t.kill()
                    return t
                except Exception:
                    _logger.exception("Exception in ScaleComponent.__init__.make_task")
                    raise

            self._update_scale_type_control_task = make_task(self._update_scale_type_control)
            self._update_root_note_control_task = make_task(self._update_root_note_control)

            self.__on_scale_type_changed_in_song.subject = self.song
            self.__on_root_note_changed_in_song.subject = self.song

            self.__on_scale_type_changed_in_song()
            self.__on_root_note_changed_in_song()

        except Exception:
            _logger.exception("Exception in ScaleComponent.__init__")
            raise

    @scale_type_control.value
    def scale_type_control(self, value, _):
        try:
            if value in range(len(SCALE_NAMES)):
                scale_name = SCALE_NAMES[value]
                if scale_name is None:
                    return
                current = getattr(self.song, "scale_name", None)
                if current != scale_name:
                    self.song.scale_name = scale_name
        except Exception:
            _logger.exception("Exception in ScaleComponent.scale_type_control handler")
            raise

    @root_note_control.value
    def root_note_control(self, value, _):
        try:
            if value in range(12):
                current = getattr(self.song, "root_note", None)
                if current != value:
                    self.song.root_note = value
        except Exception:
            _logger.exception("Exception in ScaleComponent.root_note_control handler")
            raise

    def _update_scale_type_control(self):
        try:
            song_scale = getattr(self.song, "scale_name", None)
            if song_scale in SCALE_NAMES:
                idx = SCALE_NAMES.index(song_scale)
                self.scale_type_control.value = idx
        except Exception:
            _logger.exception("Exception in ScaleComponent._update_scale_type_control")
            raise

    def _update_root_note_control(self):
        try:
            rn = getattr(self.song, "root_note", None)
            self.root_note_control.value = rn
        except Exception:
            _logger.exception("Exception in ScaleComponent._update_root_note_control")
            raise

    @listens("scale_name")
    def __on_scale_type_changed_in_song(self):
        try:
            self._update_scale_type_control_task.restart()
        except Exception:
            _logger.exception("Exception in ScaleComponent.__on_scale_type_changed_in_song")
            raise

    @listens("root_note")
    def __on_root_note_changed_in_song(self):
        try:
            self._update_root_note_control_task.restart()
        except Exception:
            _logger.exception("Exception in ScaleComponent.__on_root_note_changed_in_song")
            raise
