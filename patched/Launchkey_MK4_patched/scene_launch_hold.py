from __future__ import annotations

from ableton.v3.base import depends, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl

from .mk4_log import get_logger
_logger = get_logger("scene_launch_hold")

HOLD_TIME_S = 0.35


class SceneLaunchHoldComponent(Component):
    scene_launch_button = ButtonControl()

    @depends(session_ring=None, song=None)
    def __init__(self, session_ring=None, song=None, *a, **k):
        super().__init__(*a, **k)

        self._session_ring = session_ring
        self._song = song

        self._session = None  # will be injected via set_session_component()
        self._held = False

        _logger.debug(
            "init: session_ring=%s song=%s hold_time=%.3f",
            type(self._session_ring).__name__ if self._session_ring else None,
            type(self._song).__name__ if self._song else None,
            HOLD_TIME_S,
        )

        self._hold_task = self._tasks.add(
            task.sequence(task.wait(HOLD_TIME_S), task.run(self._on_hold))
        )
        self._hold_task.kill()

    def set_session_component(self, session):
        self._session = session
        _logger.debug("set_session_component: session=%s", type(session).__name__ if session else None)

    def _set_delete_modifier(self, enabled: bool):
        has_method = bool(self._session and hasattr(self._session, "set_delete_modifier"))
        _logger.debug("_set_delete_modifier(%s): session=%s has_method=%s",
                      enabled,
                      type(self._session).__name__ if self._session else None,
                      has_method)
        if has_method:
            self._session.set_delete_modifier(bool(enabled))

    def _scene_index_in_song(self) -> int | None:
        return int(self._session_ring.scene_offset) if self._session_ring else None

    def _fire_scene_0_in_ring(self):
        if not self._song:
            _logger.debug("_fire_scene_0_in_ring: song=None -> skip")
            return

        scene_idx = self._scene_index_in_song()
        scenes = getattr(self._song, "scenes", None)
        if scene_idx is None or not scenes:
            _logger.debug("_fire_scene_0_in_ring: scene_idx=%s scenes=%s -> skip", scene_idx, bool(scenes))
            return

        if 0 <= scene_idx < len(scenes):
            _logger.debug("_fire_scene_0_in_ring: firing scene_idx=%d", scene_idx)
            scenes[scene_idx].fire()

    def _delete_allowed_now(self) -> bool:
        # Without control_surface, do a minimal “safe” rule:
        # only allow delete if we actually have a session component wired.
        allowed = self._session is not None
        _logger.debug("_delete_allowed_now: session_wired=%s -> %s", bool(self._session), allowed)
        return allowed

    def _on_hold(self):
        self._held = True
        _logger.debug("_on_hold: held=True; checking delete_allowed")
        if self._delete_allowed_now():
            _logger.debug("_on_hold: arming delete modifier")
            self._set_delete_modifier(True)
        else:
            _logger.debug("_on_hold: NOT arming delete modifier")

    @scene_launch_button.pressed
    def scene_launch_button(self, _):
        _logger.debug("scene_launch_button.pressed: held was=%s", self._held)
        self._held = False
        self._set_delete_modifier(False)
        self._hold_task.restart()

    @scene_launch_button.released
    def scene_launch_button(self, _):
        _logger.debug("scene_launch_button.released: held=%s", self._held)
        self._hold_task.kill()
        was_held = self._held
        self._set_delete_modifier(False)

        if not was_held:
            _logger.debug("scene_launch_button.released: TAP -> firing scene")
            self._fire_scene_0_in_ring()
        else:
            _logger.debug("scene_launch_button.released: HOLD -> no scene fire")
