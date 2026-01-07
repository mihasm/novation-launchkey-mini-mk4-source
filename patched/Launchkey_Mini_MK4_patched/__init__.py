# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: '..\\..\\..\\output\\Live\\win_64_static\\Release\\python-bundle\\MIDI Remote Scripts\\Launchkey_Mini_MK4\\__init__.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2025-08-26 07:19:57 UTC (1756192797)

from ableton.v3.control_surface.capabilities import AUTO_LOAD_KEY, CONTROLLER_ID_KEY, NOTES_CC, PORTS_KEY, SCRIPT, SYNC, controller_id, inport, outport
from Launchkey_MK4_patched.__init__ import LaunchkeyCommonControlSurface, create_launchkey_specification, midi
from .elements import Elements
from .mappings import create_mappings
def get_capabilities():
    return {CONTROLLER_ID_KEY: controller_id(
        vendor_id=4661,
        product_ids=[321, 322],
        model_name=['Launchkey Mini MK4 25 patched', 'Launchkey Mini MK4 37 patched']),
    PORTS_KEY: [inport(props=[NOTES_CC]),
    inport(props=[NOTES_CC, SCRIPT]),
    outport(props=[]),
    outport(props=[NOTES_CC, SYNC, SCRIPT])], 
    AUTO_LOAD_KEY: True}
def create_instance(c_instance):
    return Launchkey_Mini_MK4(specification=create_launchkey_specification(Elements, create_mappings, midi.MINI_MK4_SYSEX_HEADER), c_instance=c_instance)
class Launchkey_Mini_MK4(LaunchkeyCommonControlSurface):
    # return None
    pass