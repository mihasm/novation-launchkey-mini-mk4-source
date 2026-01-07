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
    _logger.debug("ENTER get_capabilities()")
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
        _logger.debug("RETURN get_capabilities(): %r", caps)
        return caps
    except Exception:
        _logger.exception("Exception in get_capabilities")
        raise


def create_instance(c_instance):
    _logger.debug("ENTER create_instance(c_instance=%r)", c_instance)
    try:
        _logger.debug("Creating ControlSurfaceSpecification via create_launchkey_specification(...)")
        spec = create_launchkey_specification(Elements, create_mappings, midi.MK4_SYSEX_HEADER)
        _logger.debug("Specification created: %r", spec)

        _logger.debug("Instantiating Launchkey_MK4(specification=..., c_instance=...)")
        inst = Launchkey_MK4(
            specification=spec,
            c_instance=c_instance,
        )
        _logger.debug("RETURN create_instance(): %r", inst)
        return inst
    except Exception:
        _logger.exception("Exception in create_instance")
        raise


def create_launchkey_specification(elements_type, create_mappings_function, sysex_header):
    _logger.debug(
        "ENTER create_launchkey_specification(elements_type=%r, create_mappings_function=%r, sysex_header=%r)",
        elements_type,
        create_mappings_function,
        sysex_header,
    )
    try:
        _logger.debug("Building elements_type partial(elements_type, sysex_header)")
        elements_ctor = partial(elements_type, sysex_header)

        _logger.debug("Creating skin via create_skin(skin=Skin, colors=Rgb)")
        skin = create_skin(skin=Skin, colors=Rgb)

        _logger.debug("Building hello_messages/goodbye_messages")
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

        _logger.debug("Building component_map")
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

        _logger.debug("Creating ControlSurfaceSpecification(...)")
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

        _logger.debug("RETURN create_launchkey_specification(): %r", spec)
        return spec
    except Exception:
        _logger.exception("Exception in create_launchkey_specification")
        raise


def pitch_provider_for_track(track, instrument_finder):
    _logger.debug("ENTER pitch_provider_for_track(track=%r, instrument_finder=%r)", track, instrument_finder)
    try:
        if liveobj_valid(track) and track.has_midi_input:
            _logger.debug("Track valid and has MIDI input")
            if liveobj_valid(instrument_finder.drum_group):
                _logger.debug("instrument_finder.drum_group valid -> RETURN 'Drum_Group'")
                return "Drum_Group"
            _logger.debug("No drum_group -> RETURN 'Keyboard'")
            return "Keyboard"
        _logger.debug("Track invalid or no MIDI input -> RETURN None")
        return None
    except Exception:
        _logger.exception("Exception in pitch_provider_for_track")
        raise


class LaunchkeyCommonControlSurface(ControlSurface):
    def __init__(self, *a, **k):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.__init__(a=%r, k=%r)", a, k)
        try:
            super().__init__(*a, **k)
            _logger.debug("super().__init__ completed")

            _logger.debug("Creating _enable_main_modes_task")
            self._enable_main_modes_task = self._tasks.add(
                task.sequence(
                    task.wait(0.2),
                    task.run(self._enable_main_modes),
                )
            )
            _logger.debug("_enable_main_modes_task created: %r", self._enable_main_modes_task)

            _logger.debug("Killing _enable_main_modes_task initially")
            self._enable_main_modes_task.kill()
            _logger.debug("_enable_main_modes_task killed")

        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.__init__")
            raise

    def port_settings_changed(self):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.port_settings_changed()")
        try:
            _logger.debug("Sending disconnect connection_message (port settings changed)")
            self._send_midi(midi.make_connection_message(self.specification.sysex_header, connect=False))

            _logger.debug("Calling super().port_settings_changed()")
            super().port_settings_changed()
            _logger.debug("super().port_settings_changed() completed")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.port_settings_changed")
            raise

    def send_midi(self, midi_bytes):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.send_midi(midi_bytes=%r)", midi_bytes)
        try:
            self._send_midi(midi_bytes)
            _logger.debug("_send_midi completed")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.send_midi")
            raise

    def setup(self):
        try:
            super().setup()

            hold = self.component_map.get("Scene_Launch_Hold")
            session = self.component_map.get("Session")

            _logger.debug(
                "Wiring Scene_Launch_Hold -> Session: hold=%s session=%s",
                type(hold).__name__ if hold else None,
                type(session).__name__ if session else None,
            )

            if hold and session and hasattr(hold, "set_session_component"):
                hold.set_session_component(session)

        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.setup")
            raise

    def target_track_changed(self, _):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.target_track_changed(_) -> _update_sequencer()")
        try:
            self._update_sequencer()
            _logger.debug("_update_sequencer completed")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.target_track_changed")
            raise

    def drum_group_changed(self, _):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.drum_group_changed(_) -> _update_sequencer()")
        try:
            self._update_sequencer()
            _logger.debug("_update_sequencer completed")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.drum_group_changed")
            raise

    def identification_state_changed(self, state):
        _logger.debug("ENTER LaunchkeyCommonControlSurface.identification_state_changed(state=%r)", state)
        try:
            if state:
                _logger.debug("state=True: updating display and modes, sending disable daw label popup")
                self.display.display(default_label_content())
                self.component_map["Main_Pad_Modes"].selected_mode = "null_0"
                self.send_midi(midi.make_disable_daw_label_popup(self.specification.sysex_header))

            _logger.debug("Restarting _enable_main_modes_task")
            self._enable_main_modes_task.restart()
            _logger.debug("_enable_main_modes_task restarted")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface.identification_state_changed")
            raise

    def _enable_main_modes(self):
        _logger.debug("ENTER LaunchkeyCommonControlSurface._enable_main_modes()")
        try:
            state = self._identification.is_identified
            _logger.debug("Identification state: is_identified=%r", state)

            _logger.debug("Entering component_guard()")
            with self.component_guard():
                _logger.debug("Setting Main_Encoder_Modes.selected_mode='plugin'")
                self.component_map["Main_Encoder_Modes"].selected_mode = "plugin"

                _logger.debug("Enabling Main_Encoder_Modes=%r", state)
                self.component_map["Main_Encoder_Modes"].set_enabled(state)

                _logger.debug("Setting Daw_Pad_Modes.selected_mode='clip'")
                self.component_map["Daw_Pad_Modes"].selected_mode = "clip"

                _logger.debug("Setting Main_Pad_Modes.selected_mode='daw'")
                self.component_map["Main_Pad_Modes"].selected_mode = "daw"

                _logger.debug("Enabling Main_Pad_Modes=%r", state)
                self.component_map["Main_Pad_Modes"].set_enabled(state)

            _logger.debug("component_guard() exited")

            _logger.debug("Setting can_auto_arm=%r", state)
            self.set_can_auto_arm(state)
            _logger.debug("set_can_auto_arm completed")
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._enable_main_modes")
            raise

    def _update_sequencer(self, *_):
        _logger.debug("ENTER LaunchkeyCommonControlSurface._update_sequencer(_=%r)", _)
        try:
            main_pad = self.component_map["Main_Pad_Modes"].selected_mode
            daw_pad = self.component_map["Daw_Pad_Modes"].selected_mode
            seq_mode = self.component_map["Sequencer_Modes"].selected_mode

            _logger.debug(
                "Mode state: Main_Pad_Modes=%r Daw_Pad_Modes=%r Sequencer_Modes=%r",
                main_pad,
                daw_pad,
                seq_mode,
            )

            if main_pad == "daw" and daw_pad == "sequencer" and seq_mode == "default":
                _logger.debug("Sequencer active condition met -> computing pitch_provider")
                pitch_provider = pitch_provider_for_track(
                    self._target_track.target_track,
                    self.instrument_finder,
                )
                _logger.debug("pitch_provider=%r", pitch_provider)

                provider_component = self.component_map[pitch_provider] if pitch_provider else None
                _logger.debug("provider_component resolved: %r", provider_component)

                _logger.debug("Setting Step_Sequence pitch provider")
                self.component_map["Step_Sequence"].set_pitch_provider(provider_component)

                enable_keyboard = (pitch_provider == "Keyboard")
                _logger.debug("Sending enable_keyboard_message(enable=%r)", enable_keyboard)
                self._send_midi(midi.make_enable_keyboard_message(enable=enable_keyboard))
            else:
                _logger.debug("Sequencer not in active condition -> disable keyboard")
                self._send_midi(midi.make_enable_keyboard_message(enable=False))

            _logger.debug("_update_sequencer completed")
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
        _logger.debug("ENTER __on_main_pad_mode_changed(selected_mode=%r)", selected_mode)
        try:
            _logger.debug("set_can_update_controlled_track(%r)", selected_mode == "drum")
            self.set_can_update_controlled_track(selected_mode == "drum")

            _logger.debug("Calling _update_sequencer() due to main pad mode change")
            self._update_sequencer()

            _logger.debug("__on_main_pad_mode_changed completed")
        except Exception:
            _logger.exception("Exception in __on_main_pad_mode_changed")
            raise

    def _get_additional_dependencies(self):
        _logger.debug("ENTER LaunchkeyCommonControlSurface._get_additional_dependencies()")
        try:
            _logger.debug("Creating SequencerClip(target_track=self._target_track)")
            sequencer_clip = self.register_disconnectable(SequencerClip(target_track=self._target_track))
            _logger.debug("SequencerClip registered: %r", sequencer_clip)

            deps = {"sequencer_clip": const(sequencer_clip)}
            _logger.debug("RETURN additional dependencies: %r", deps)
            return deps
        except Exception:
            _logger.exception("Exception in LaunchkeyCommonControlSurface._get_additional_dependencies")
            raise


class Launchkey_MK4_patched(LaunchkeyCommonControlSurface):
    def on_identified(self, response_bytes):
        _logger.debug("ENTER Launchkey_MK4.on_identified(response_bytes=%r)", response_bytes)
        try:
            _logger.debug("Calling super().on_identified(response_bytes)")
            super().on_identified(response_bytes)
            _logger.debug("super().on_identified completed")

            has_faders = response_bytes[6] not in midi.SMALL_MODEL_ID_BYTES
            _logger.debug("Computed has_faders=%r (response_bytes[6]=%r)", has_faders, response_bytes[6])

            _logger.debug("Entering component_guard() for fader-dependent enable flags")
            with self.component_guard():
                _logger.debug("Setting Fader_Button_Modes enabled=%r", has_faders)
                self.component_map["Fader_Button_Modes"].set_enabled(has_faders)

                _logger.debug("Setting Volume_Mixer enabled=%r", has_faders)
                self.component_map["Volume_Mixer"].set_enabled(has_faders)

            _logger.debug("on_identified completed")
        except Exception:
            _logger.exception("Exception in Launchkey_MK4.on_identified")
            raise
