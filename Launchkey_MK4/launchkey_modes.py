# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: '..\\..\\..\\output\\Live\\win_64_static\\Release\\python-bundle\\MIDI Remote Scripts\\Launchkey_MK4\\launchkey_modes.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2025-12-15 14:43:45 UTC (1765809825)

from ableton.v3.control_surface.mode import ModesComponent
class LaunchkeyModesComponent(ModesComponent):
    pass
    def _handle_mode_selection_control_value(self, value):
        if self.is_enabled():
            if value < len(self.modes):
                self.previous_mode = self.selected_mode
                mode = self.modes[value]
                self._get_mode_behaviour(mode).press_immediate(self, mode)