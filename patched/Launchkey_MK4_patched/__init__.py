from __future__ import annotations

import logging
import os
import sys
import traceback
from functools import partial

from ableton.v3.base import const, listens, task
from ableton.v3.control_surface import ControlSurface, ControlSurfaceSpecification, create_skin
from ableton.v3.control_surface.capabilities import (
    AUTO_LOAD_KEY,
    CONTROLLER_ID_KEY,
    NOTES_CC,
    PORTS_KEY,
    SCRIPT,
    SYNC,
    controller_id,
    inport,
    outport,
)
from ableton.v3.control_surface.components import DEFAULT_DRUM_TRANSLATION_CHANNEL, MixerComponent
from ableton.v3.live import liveobj_valid

from . import midi
from .auto_arm import AutoArmComponent
from .colors import Rgb
from .cue_point import CuePointComponent
from .display import default_label_content, display_specification
from .drum_group import DrumGroupComponent
from .elements import Elements
from .encoder_touch import EncoderTouchComponent
from .keyboard import KeyboardComponent
from .mappings import create_mappings
from .scale import ScaleComponent
from .scene_launch_hold import SceneLaunchHoldComponent
from .session import SessionComponent
from .session_navigation import SessionNavigationComponent
from .skin import Skin
from .step_sequence import SequencerClip, StepSequenceComponent
from .transport import TransportComponent
from .zoom import ZoomComponent


from .mk4_log import get_logger
_logger = get_logger("init")

def get_capabilities():
    try:
        caps = {
            CONTROLLER_ID_KEY: controller_id(
                vendor_id=4661,
                product_ids=[323, 324, 325, 326],
                model_name=["Launchkey MK4 25 patched", "Launchkey MK4 37 patched", "Launchkey MK4 49 patched", "Launchkey MK4 61 patched"],
            ),
            PORTS_KEY: [
                inport(props=[NOTES_CC]),
                inport(props=[NOTES_CC, SCRIPT]),
                outport(props=[]),
                outport(props=[NOTES_CC, SYNC, SCRIPT]),
            ],
            AUTO_LOAD_KEY: True,
        }
        return caps
    except Exception:
        _logger.exception("Exception in get_capabilities")
        raise


def create_instance(c_instance):
    try:
        spec = create_launchkey_specification(Elements, create_mappings, midi.MK4_SYSEX_HEADER)
        inst = Launchkey_MK4_patched(
            specification=spec,
            c_instance=c_instance,
        )
        return inst
    except Exception:
        _logger.exception("Exception in create_instance")
        raise


def create_launchkey_specification(elements_type, create_mappings_function, sysex_header):
    try:
        elements_ctor = partial(elements_type, sysex_header)
        skin = create_skin(skin=Skin, colors=Rgb)

        hello_messages = (
            midi.make_connection_message(sysex_header),
            midi.make_enable_touch_output_message(),
            midi.make_enable_drum_pads_message(),
        )
        goodbye_messages = (
            midi.make_connection_message(sysex_header, connect=False),
            midi.make_enable_drum_pads_message(enable=False),
            midi.make_enable_keyboard_message(enable=True),
        )

        component_map = {
            "Cue_Point": CuePointComponent,
            "Drum_Group": DrumGroupComponent,
            "Encoder_Touch": EncoderTouchComponent,
            "Keyboard": KeyboardComponent,
            "Scale": ScaleComponent,
            "Scene_Launch_Hold": SceneLaunchHoldComponent,
            "Session": SessionComponent,
            "Session_Navigation": SessionNavigationComponent,
            "Step_Sequence": StepSequenceComponent,
            "Transport": TransportComponent,
            "Volume_Mixer": partial(MixerComponent, name="Volume_Mixer"),
            "Zoom": ZoomComponent,
        }

        spec = ControlSurfaceSpecification(
            elements_type=elements_ctor,
            control_surface_skin=skin,
            num_tracks=8,
            num_scenes=2,
            include_auto_arming=True,
            link_session_ring_to_track_selection=True,
            feedback_channels=[DEFAULT_DRUM_TRANSLATION_CHANNEL],
            playing_feedback_velocity=Rgb.WHITE.midi_value,
            recording_feedback_velocity=Rgb.RED.midi_value,
            identity_response_id_bytes=(0, 32, 41, -1, 1, 0, 1),
            sysex_header=sysex_header,
            hello_messages=hello_messages,
            goodbye_messages=goodbye_messages,
            create_mappings_function=create_mappings_function,
            auto_arm_component_type=AutoArmComponent,
            component_map=component_map,
            display_specification=display_specification,
        )

        return spec
    except Exception:
        _logger.exception("Exception in create_launchkey_specification")
        raise


def pitch_provider_for_track(track, instrument_finder):
    try:
        if liveobj_valid(track) and track.has_midi_input:
            if liveobj_valid(instrument_finder.drum_group):
                return "Drum_Group"
            return "Keyboard"
        return None
    except Exception:
        _logger.exception("Exception in pitch_provider_for_track")
        raise


class LaunchkeyCommonControlSurface(ControlSurface):
    def __init__(self, *a, **k):
        try:
            super().__init__(*a, **k)
            self._enable_main_modes_task = self._tasks.add(
                task.sequence(
                    task.wait(0.2),
                    task.run(self._enable_main_modes),
                )
            )
            self._enable_main_modes_task.kill()

        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.__init__")
            raise

    def port_settings_changed(self):
        try:
            self._send_midi(midi.make_connection_message(self.specification.sysex_header, connect=False))
            super().port_settings_changed()
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.port_settings_changed")
            raise

    def send_midi(self, midi_bytes):
        try:
            self._send_midi(midi_bytes)
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.send_midi")
            raise

    def setup(self):
        try:
            super().setup()

            hold = self.component_map.get("Scene_Launch_Hold")
            session = self.component_map.get("Session")

            if hold and session and hasattr(hold, "set_session_component"):
                hold.set_session_component(session)

        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.setup")
            raise

    def target_track_changed(self, _):
        try:
            self._update_sequencer()
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.target_track_changed")
            raise

    def drum_group_changed(self, _):
        try:
            self._update_sequencer()
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.drum_group_changed")
            raise

    def identification_state_changed(self, state):
        try:
            if state:
                self.display.display(default_label_content())
                self.component_map["Main_Pad_Modes"].selected_mode = "null_0"
                self.send_midi(midi.make_disable_daw_label_popup(self.specification.sysex_header))

            self._enable_main_modes_task.restart()
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.identification_state_changed")
            raise

    def _enable_main_modes(self):
        try:
            state = self._identification.is_identified

            with self.component_guard():
                self.component_map["Main_Encoder_Modes"].selected_mode = "plugin"
                self.component_map["Main_Encoder_Modes"].set_enabled(state)
                self.component_map["Daw_Pad_Modes"].selected_mode = "clip"
                self.component_map["Main_Pad_Modes"].selected_mode = "daw"
                self.component_map["Main_Pad_Modes"].set_enabled(state)

            self.set_can_auto_arm(state)
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._enable_main_modes")
            raise

    def _update_sequencer(self, *_):
        try:
            main_pad = self.component_map["Main_Pad_Modes"].selected_mode
            daw_pad = self.component_map["Daw_Pad_Modes"].selected_mode
            seq_mode = self.component_map["Sequencer_Modes"].selected_mode

            if main_pad == "daw" and daw_pad == "sequencer" and seq_mode == "default":
                pitch_provider = pitch_provider_for_track(
                    self._target_track.target_track,
                    self.instrument_finder,
                )

                provider_component = self.component_map[pitch_provider] if pitch_provider else None
                self.component_map["Step_Sequence"].set_pitch_provider(provider_component)

                enable_keyboard = (pitch_provider == "Keyboard")
                self._send_midi(midi.make_enable_keyboard_message(enable=enable_keyboard))
            else:
                self._send_midi(midi.make_enable_keyboard_message(enable=False))

        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._update_sequencer")
            raise

    @staticmethod
    def _should_include_element_in_background(element):
        #_logger.debug("ENTER LaunchkeyCommonControlSurface._should_include_element_in_background(element=%r)", element)
        try:
            res = "Keyboard" not in element.name
            #_logger.debug("RETURN _should_include_element_in_background: %r (element.name=%r)", res, getattr(element, "name", None))
            return res
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._should_include_element_in_background")
            raise

    @listens("selected_mode")
    def __on_main_pad_mode_changed(self, selected_mode):
        try:
            self.set_can_update_controlled_track(selected_mode == "drum")
            self._update_sequencer()
        except Exception:
            _logger.exception("Exception in __on_main_pad_mode_changed")
            raise

    def _get_additional_dependencies(self):
        try:
            sequencer_clip = self.register_disconnectable(SequencerClip(target_track=self._target_track))
            deps = {"sequencer_clip": const(sequencer_clip)}
            return deps
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._get_additional_dependencies")
            raise


class Launchkey_MK4_patched(LaunchkeyCommonControlSurface):
    def on_identified(self, response_bytes):
        try:
            super().on_identified(response_bytes)

            has_faders = response_bytes[6] not in midi.SMALL_MODEL_ID_BYTES

            with self.component_guard():
                self.component_map["Fader_Button_Modes"].set_enabled(has_faders)
                self.component_map["Volume_Mixer"].set_enabled(has_faders)

        except Exception:
            _logger.exception("Exception in Launchkey_MK4.on_identified")
            raise
