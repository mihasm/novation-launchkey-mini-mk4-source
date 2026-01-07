# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: '..\\..\\..\\output\\Live\\win_64_static\\Release\\python-bundle\\MIDI Remote Scripts\\Launchkey_Mini_MK4\\mappings.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2025-08-26 07:19:57 UTC (1756192797)

from Launchkey_MK4_patched.mappings import create_launchkey_common_mappings
def create_mappings(control_surface):
    mappings = create_launchkey_common_mappings(control_surface)
    mappings['Transport'] = dict(play_toggle_button='play_button', play_pause_button='play_button_with_shift', capture_midi_button='record_button_with_shift')
    mappings['View_Control'] = dict(prev_track_button='track_left_button', next_track_button='track_right_button')
    return mappings