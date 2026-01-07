from ableton.v3.control_surface.elements import ButtonElement
class MultiButtonElement(ButtonElement):
    pass
    def __init__(self, *a, **k):
        self._secondary_button = SecondaryButtonElement(self, k.pop('secondary_identifier'), **k)
        super().__init__(*a, is_private=True, **k)
    def send_value(self, value, force=False, channel=None):
        super().send_value(value, force=force, channel=channel)
        self._secondary_button.send_value(value, force=force, channel=channel)
class SecondaryButtonElement(ButtonElement):
    pass
    def __init__(self, parent, *a, **k):
        super().__init__(*a, is_private=True, **k)
        self._parent = parent
    def receive_value(self, value):
        super().receive_value(value)
        self._parent.receive_value(value)
    def script_wants_forwarding(self):
        return True