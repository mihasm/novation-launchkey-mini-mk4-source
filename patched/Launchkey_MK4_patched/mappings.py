from __future__ import annotations

import logging
import os
import sys
import traceback

from ableton.v3.control_surface import MOMENTARY_DELAY
from ableton.v3.control_surface.mode import (
    EventDescription,
    ImmediateBehaviour,
    ShowDetailClipMode,
    make_reenter_behaviour,
    select_mode_on_event_change,
)

from .display import cancel_temp_screens
from .launchkey_modes import LaunchkeyModesComponent
from .midi import SET_RELATIVE_ENCODER_MODE


from .mk4_log import get_logger
_logger = get_logger("mappings")


def activate_note_settings(control_surface):
    try:
        note_editor = control_surface.component_map["Step_Sequence"].note_editor

        def inner(modes, mode_name):
            try:
                encoder_modes = control_surface.component_map["Main_Encoder_Modes"]

                def on_event(*_):
                    try:
                        if not note_editor.active_steps:
                            modes.pop_mode(mode_name)
                            return

                        selected_mode = getattr(modes, "selected_mode", None)
                        encoder_selected_mode = getattr(encoder_modes, "selected_mode", None)

                        if (
                            selected_mode != mode_name
                            and encoder_selected_mode in ("mixer", "plugin", "sends", "transport")
                        ):
                            modes.push_mode(mode_name, delay=MOMENTARY_DELAY)
                    except Exception:
                        _logger.exception("Exception in activate_note_settings.inner.on_event")
                        raise

                modes.register_slot(note_editor, on_event, "active_steps")

            except Exception:
                _logger.exception("Exception in activate_note_settings.inner")
                raise

        return inner

    except Exception:
        _logger.exception("Exception in activate_note_settings")
        raise


def set_playhead_enabled(control_surface, enabled):
    try:
        step_seq = control_surface.component_map["Step_Sequence"]

        # IMPORTANT: do NOT disable the Step_Sequence component.
        # Toggle only the playhead/overlay if such API exists.
        if hasattr(step_seq, "set_playhead_enabled"):
            step_seq.set_playhead_enabled(enabled)
            return

        # Some implementations expose a playhead object.
        if hasattr(step_seq, "playhead"):
            ph = step_seq.playhead
            if hasattr(ph, "set_enabled"):
                ph.set_enabled(enabled)
                return

        _logger.warning(
            "No playhead toggle API found on Step_Sequence; NOT changing Step_Sequence enabled state."
        )

    except Exception:
        _logger.exception("Exception in set_playhead_enabled")
        raise


def set_relative_encoder_mode(control_surface):
    try:
        def _send():
            try:
                control_surface.send_midi(SET_RELATIVE_ENCODER_MODE)
            except Exception:
                _logger.exception("Exception in set_relative_encoder_mode._send")
                raise

        return _send

    except Exception:
        _logger.exception("Exception in set_relative_encoder_mode")
        raise


def make_relative_encoder_mode_behavior(control_surface):
    try:
        behavior = make_reenter_behaviour(
            ImmediateBehaviour,
            on_reenter=set_relative_encoder_mode(control_surface),
        )
        return behavior

    except Exception:
        _logger.exception("Exception in make_relative_encoder_mode_behavior")
        raise


def create_launchkey_common_mappings(control_surface):
    try:
        mappings = {}

        mappings["View_Based_Recording"] = dict(record_button="record_button")

        mappings["Scale"] = dict(
            scale_type_control="scale_type_element",
            root_note_control="root_note_element",
        )

        mappings["Keyboard"] = dict(matrix="keyboard")

        mappings["Encoder_Touch"] = dict(touch_controls="encoder_touch_elements")

        mappings["Lower_Pad_Modes"] = dict(
            enable=False,
            is_private=True,
            support_momentary_mode_cycling=False,
            cycle_mode_button="pad_function_button",
            clip_launch=None,
            stop=dict(component="Session", stop_track_clip_buttons="lower_pads"),
            mute=dict(component="Mixer", mute_buttons="lower_pads"),
            solo=dict(component="Mixer", solo_buttons="lower_pads"),
        )

        # Logged callables used inside mappings (instead of anonymous lambdas)
        def _set_playhead_disabled():
            try:
                set_playhead_enabled(control_surface, False)
            except Exception:
                _logger.exception("Exception in _set_playhead_disabled")
                raise

        def _set_playhead_enabled_true():
            try:
                set_playhead_enabled(control_surface, True)
            except Exception:
                _logger.exception("Exception in _set_playhead_enabled_true")
                raise

        def _cancel_temp_screens_now():
            try:
                cancel_temp_screens(control_surface.elements)
            except Exception:
                _logger.exception("Exception in _cancel_temp_screens_now")
                raise

        mappings["Sequencer_Modes"] = dict(
            enable=False,
            is_private=True,
            support_momentary_mode_cycling=False,
            cycle_mode_button="scene_launch_button",
            default=dict(
                modes=[
                    dict(
                        component="Step_Sequence",
                        step_buttons="main_pads",
                        prev_page_button="pad_up_button",
                        next_page_button="pad_down_button",
                        note_copy_button="pad_function_button",
                        double_button="pad_down_button_with_pad_function",
                    ),
                    dict(
                        component="Modifier_Background",
                        pad_function_button="pad_function_button",
                    ),
                    _set_playhead_disabled,
                ],
                selector=select_mode_on_event_change(
                    EventDescription(
                        subject=control_surface.component_map["Session"],
                        event_name="clip_selected",
                    )
                ),
            ),
            clip_select=dict(
                modes=[
                    dict(component="Session", clip_select_buttons="main_pads"),
                    dict(
                        component="Session_Navigation",
                        up_button="pad_up_button",
                        down_button="pad_down_button",
                    ),
                    _set_playhead_enabled_true,
                    _cancel_temp_screens_now,
                ]
            ),
        )

        mappings["Daw_Pad_Modes"] = dict(
            enable=False,
            is_private=True,
            clip=dict(
                modes=[
                    dict(
                        component="Session",
                        clip_launch_buttons="main_pads",
                        #scene_0_launch_button="scene_launch_button",
                    ),
                    dict(component="Scene_Launch_Hold"),
                    dict(
                        component="Session_Navigation",
                        up_button="pad_up_button",
                        down_button="pad_down_button",
                    ),
                    dict(component="Lower_Pad_Modes"),
                ]
            ),
            sequencer=dict(component="Sequencer_Modes"),
        )

        mappings["Scene_Launch_Hold"] = dict(
            scene_launch_button="scene_launch_button",
        )

        def _cycle_daw_pad_modes():
            try:
                control_surface.component_map["Daw_Pad_Modes"].cycle_mode()
            except Exception:
                _logger.exception("Exception in _cycle_daw_pad_modes")
                raise

        mappings["Main_Pad_Modes"] = dict(
            modes_component_type=LaunchkeyModesComponent,
            enable=False,
            is_private=True,
            mode_selection_control="pad_mode_element",
            null_0=None,
            null_1=None,
            daw=dict(
                component="Daw_Pad_Modes",
                behaviour=make_reenter_behaviour(
                    ImmediateBehaviour,
                    on_reenter=_cycle_daw_pad_modes,
                ),
            ),
            null_3=None,
            chord=None,
            custom_1=None,
            custom_2=None,
            custom_3=None,
            custom_4=None,
            null_9=None,
            null_10=None,
            null_11=None,
            null_12=None,
            arp=None,
            chord_map=None,
            drum=dict(
                component="Drum_Group",
                matrix="drum_pads",
                scroll_page_up_button="pad_up_button",
                scroll_page_down_button="pad_down_button",
            ),
        )

        mappings["Mixer_Encoder_Modes"] = dict(
            enable=False,
            is_private=True,
            level_button="encoder_up_button",
            pan_button="encoder_down_button",
            level=dict(component="Mixer", volume_controls="encoders"),
            pan=dict(component="Mixer", pan_controls="encoders"),
        )

        mappings["Main_Encoder_Modes"] = dict(
            modes_component_type=LaunchkeyModesComponent,
            enable=False,
            is_private=True,
            mode_selection_control="encoder_mode_element",
            null_0=None,
            mixer=dict(
                modes=[
                    dict(component="Mixer_Encoder_Modes"),
                    set_relative_encoder_mode(control_surface),
                ],
                behaviour=make_relative_encoder_mode_behavior(control_surface),
            ),
            plugin=dict(
                modes=[
                    dict(
                        component="Device",
                        parameter_controls="encoders",
                        prev_bank_button="encoder_up_button",
                        next_bank_button="encoder_down_button",
                    ),
                    set_relative_encoder_mode(control_surface),
                ],
                behaviour=make_relative_encoder_mode_behavior(control_surface),
            ),
            null_3=None,
            sends=dict(
                modes=[
                    dict(
                        component="Mixer",
                        send_controls="encoders",
                        prev_send_index_button="encoder_up_button",
                        next_send_index_button="encoder_down_button",
                    ),
                    set_relative_encoder_mode(control_surface),
                ],
                behaviour=make_relative_encoder_mode_behavior(control_surface),
            ),
            transport=dict(
                modes=[
                    dict(
                        component="Transport",
                        arrangement_position_encoder="encoders_raw[0]",
                        loop_start_encoder="encoders_raw[3]",
                        loop_length_encoder="encoders_raw[4]",
                        tempo_coarse_encoder="encoders_raw[7]",
                        set_cue_button="encoder_up_button",
                    ),
                    dict(
                        component="Zoom",
                        horizontal_zoom_encoder="encoders_raw[1]",
                        vertical_zoom_encoder="encoders_raw[2]",
                    ),
                    dict(component="Cue_Point", encoder="encoders_raw[5]"),
                ]
            ),
            custom_1=None,
            custom_2=None,
            custom_3=None,
            custom_4=None,
        )
        _logger.debug("Configured mappings['Main_Encoder_Modes']")

        def _note_settings_inactive():
            _logger.debug(
                "CALL _note_settings_inactive -> schedule_message(delay=%r, cancel_temp_screens, elements)",
                MOMENTARY_DELAY,
            )
            try:
                control_surface.schedule_message(
                    MOMENTARY_DELAY, cancel_temp_screens, control_surface.elements
                )
            except Exception:
                _logger.exception("Exception in _note_settings_inactive")
                raise

        def _note_settings_active_cancel_temp_screens():
            try:
                control_surface.schedule_message(
                    0.1, cancel_temp_screens, control_surface.elements
                )
            except Exception:
                _logger.exception("Exception in _note_settings_active_cancel_temp_screens")
                raise

        mappings["Note_Settings_Modes"] = dict(
            is_private=True,
            inactive=_note_settings_inactive,
            active=dict(
                modes=[
                    dict(component="Step_Sequence", encoders="encoders"),
                    dict(
                        component="Background",
                        bg_encoder_up_button="encoder_up_button",
                        bg_encoder_down_button="encoder_down_button",
                    ),
                    ShowDetailClipMode(control_surface.application),
                    _note_settings_active_cancel_temp_screens,
                ],
                selector=activate_note_settings(control_surface),
            ),
        )

        return mappings

    except Exception:
        _logger.exception("Exception in create_launchkey_common_mappings")
        raise


def create_mappings(control_surface):
    try:
        mappings = create_launchkey_common_mappings(control_surface)

        mappings["Transport"] = dict(
            play_toggle_button="play_button",
            play_pause_button="play_button_with_shift",
            stop_button="stop_button",
            loop_button="loop_button",
            metronome_button="metronome_button",
            capture_midi_button="capture_button",
        )

        mappings["Undo_Redo"] = dict(
            undo_button="undo_button",
            redo_button="undo_button_with_shift",
        )

        mappings["Step_Sequence"] = dict(quantize_button="quantise_button")

        mappings["View_Control"] = dict(
            prev_track_button="track_left_button",
            next_track_button="track_right_button",
        )

        mappings["Session_Navigation"] = dict(
            page_left_button="shifted_track_left_button",
            page_right_button="shifted_track_right_button",
        )

        mappings["Volume_Mixer"] = dict(
            enable=False,
            volume_controls="faders",
            master_track_volume_control="master_fader",
        )

        mappings["Fader_Button_Modes"] = dict(
            enable=False,
            is_private=True,
            support_momentary_mode_cycling=False,
            cycle_mode_button="fader_button_mode_button",
            arm=dict(component="Mixer", arm_buttons="fader_buttons"),
            select=dict(component="Mixer", track_select_buttons="fader_buttons"),
        )

        return mappings

    except Exception:
        _logger.exception("Exception in create_mappings")
        raise
