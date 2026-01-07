from ableton.v3.base import depends, listens
from ableton.v3.control_surface.components import AutoArmComponent as AutoArmComponentBase
class AutoArmComponent(AutoArmComponentBase):
    pass
    @depends(session_ring=None)
    def __init__(self, session_ring=None, *a, **k):
        super().__init__(*a, **k)
        self._last_track_offset = (-1)
        self.__on_offset_changed.subject = session_ring
    @listens('offset')
    def __on_offset_changed(self, track_offset, _):
        if track_offset!= self._last_track_offset:
            self._set_auto_arm_state(False)
        self._last_track_offset = track_offset