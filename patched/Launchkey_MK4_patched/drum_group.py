from ableton.v3.base import listens
from ableton.v3.control_surface import LiveObjSkinEntry
from ableton.v3.control_surface.components import DrumGroupComponent as DrumGroupComponentBase
from ableton.v3.live import liveobj_valid
class DrumGroupComponent(DrumGroupComponentBase):
    pass
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.__on_target_track_color_changed.subject = self._target_track
    def _update_button_color(self, button):
        pad = self._pad_for_button(button)
        button.color = self._color_for_pad(pad) if pad else LiveObjSkinEntry('DrumGroup.Empty', self._target_track.target_track)
    @listens('target_track.color')
    def __on_target_track_color_changed(self):
        if not liveobj_valid(self._drum_group_device):
            self._update_led_feedback()