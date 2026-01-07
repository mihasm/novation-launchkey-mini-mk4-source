from __future__ import annotations

from ableton.v3.base import depends, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl

HOLD_TIME_S = 0.35  # tweak

class SceneLaunchHoldComponent(Component):
    scene_launch_button = ButtonControl()

    @depends(session_ring=None, song=None)
    def __init__(self, session_ring=None, song=None, *a, **k):
        super().__init__(*a, **k)
        self._session_ring = session_ring
        self._song = song
        self._held = False

        self._hold_task = self._tasks.add(
            task.sequence(
                task.wait(HOLD_TIME_S),
                task.run(self._mark_held),
            )
        )
        self._hold_task.kill()

    def _mark_held(self):
        self._held = True

    def _fire_scene_0_in_ring(self):
        # Fire the top scene of the session ring (scene index = offset + 0)
        if self._song is None or self._session_ring is None:
            return
        idx = int(self._session_ring.scene_offset)
        scenes = getattr(self._song, "scenes", None)
        if scenes and 0 <= idx < len(scenes):
            scenes[idx].fire()

    @scene_launch_button.pressed
    def scene_launch_button(self, _):
        self._held = False
        self._hold_task.restart()

    @scene_launch_button.released
    def scene_launch_button(self, _):
        self._hold_task.kill()

        # POC behavior:
        # - tap => launch
        # - hold => do nothing (swallow)
        if not self._held:
            self._fire_scene_0_in_ring()
