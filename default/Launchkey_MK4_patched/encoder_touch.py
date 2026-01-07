from functools import partial
from ableton.v3.base import listenable_property, task
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl, control_matrix
from ableton.v3.control_surface.display import Renderable
class EncoderTouchComponent(Component, Renderable):
    pass
    touch_controls = control_matrix(ButtonControl, color=None)
    last_released_index = listenable_property.managed(None)
    def __init__(self, *a, **k):
        super().__init__(*a, name='Encoder_Touch', **k)
        self._release_tasks = None
    def set_touch_controls(self, element):
        self.touch_controls.set_control_element(element)
        self._make_release_tasks()
    @touch_controls.pressed
    def touch_controls(self, control):
        self._release_tasks[control.index].kill()
    @touch_controls.released
    def touch_controls(self, control):
        self._release_tasks[control.index].restart()
    def _set_released(self, index):
        self.last_released_index = index
    def _make_release_tasks(self):
        if self._release_tasks is None and self.touch_controls.control_count:
                self._release_tasks = [self._tasks.add(task.sequence(task.wait(0.1), task.run(partial(self._set_released, i)), task.run(partial(self._set_released, None)))) for i in range(self.touch_controls.control_count)]
        for release_task in self._release_tasks:
            release_task.kill()