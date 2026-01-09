from __future__ import annotations

from ableton.v3.base import depends, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl
from ableton.v3.control_surface.display import Renderable

from .mk4_log import get_logger
_logger = get_logger("scene_launch_hold")

HOLD_TIME_S = 0.35


class SceneLaunchHoldComponent(Component, Renderable):
    scene_launch_button = ButtonControl()

    @depends(session_ring=None, song=None)
    def __init__(self, session_ring=None, song=None, *a, **k):
        super().__init__(*a, **k)

        self._session_ring = session_ring
        self._song = song

        self._session = None  # will be injected via set_session_component()
        self._held = False

        self._hold_task = self._tasks.add(
            task.sequence(task.wait(HOLD_TIME_S), task.run(self._on_hold))
        )
        self._hold_task.kill()

    def set_session_component(self, session):
        self._session = session

    def _set_delete_modifier(self, enabled: bool):
        has_method = bool(self._session and hasattr(self._session, "set_delete_modifier"))
        if has_method:
            self._session.set_delete_modifier(bool(enabled))
            # Send notification to display
            try:
                if hasattr(self, 'notifications') and hasattr(self.notifications, 'Clip'):
                    if enabled:
                        notification = getattr(self.notifications.Clip, 'delete_mode', None)
                        if notification:
                            self.notify(notification)
                    # Note: notification will automatically clear when not sent again
            except Exception as e:
                _logger.exception("_set_delete_modifier: exception sending notification: %r", e)

    def _scene_index_in_song(self) -> int | None:
        return int(self._session_ring.scene_offset) if self._session_ring else None

    def _fire_scene_0_in_ring(self):
        if not self._song:
            return

        scene_idx = self._scene_index_in_song()
        scenes = getattr(self._song, "scenes", None)
        if scene_idx is None or not scenes:
            return

        if 0 <= scene_idx < len(scenes):
            scenes[scene_idx].fire()

    def _delete_allowed_now(self) -> bool:
        # Without control_surface, do a minimal “safe” rule:
        # only allow delete if we actually have a session component wired.
        return self._session is not None

    def _on_hold(self):
        self._held = True
        if self._delete_allowed_now():
            self._set_delete_modifier(True)

    @scene_launch_button.pressed
    def scene_launch_button(self, _):
        self._held = False
        self._set_delete_modifier(False)
        self._hold_task.restart()

    @scene_launch_button.released
    def scene_launch_button(self, _):
        self._hold_task.kill()
        was_held = self._held
        self._set_delete_modifier(False)

        if not was_held:
            self._fire_scene_0_in_ring()
