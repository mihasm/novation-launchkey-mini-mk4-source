from ableton.v3.control_surface.mode import ModesComponent
class LaunchkeyModesComponent(ModesComponent):
    pass
    def _handle_mode_selection_control_value(self, value):
        if self.is_enabled():
            if value < len(self.modes):
                self.previous_mode = self.selected_mode
                mode = self.modes[value]
                self._get_mode_behaviour(mode).press_immediate(self, mode)