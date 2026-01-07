from ableton.v3.control_surface.components import ZoomComponent as ZoomComponentBase
from .internal_parameter import InternalParameterControl, register_internal_parameter
class ZoomComponent(ZoomComponentBase):
    pass
    vertical_zoom_encoder = InternalParameterControl()
    horizontal_zoom_encoder = InternalParameterControl()
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._direction = 'In'
        self.vertical_zoom_encoder.parameter = register_internal_parameter(self, 'Zoom Vertical', lambda _: self._direction)
        self.horizontal_zoom_encoder.parameter = register_internal_parameter(self, 'Zoom Horizontal', lambda _: self._direction)
    def set_vertical_zoom_encoder(self, encoder):
        self.vertical_zoom_encoder.set_control_element(encoder)
    def set_horizontal_zoom_encoder(self, encoder):
        self.horizontal_zoom_encoder.set_control_element(encoder)
    @vertical_zoom_encoder.value
    def vertical_zoom_encoder(self, value, _):
        self._do_zoom(value, self._vertical_zoom)
    @horizontal_zoom_encoder.value
    def horizontal_zoom_encoder(self, value, _):
        self._do_zoom(value, self._horizontal_zoom)
    def _do_zoom(self, value, scroller):
        if value < 0:
            self._direction = 'Out'
            scroller.scroll_up()
        else:
            self._direction = 'In'
            scroller.scroll_down()