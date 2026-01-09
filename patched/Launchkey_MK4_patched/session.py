from ableton.v3.base import depends
from ableton.v3.control_surface.components import ClipSlotComponent as ClipSlotComponentBase
from ableton.v3.control_surface.components import SessionComponent as SessionComponentBase
from ableton.v3.control_surface.components import create_sequencer_clip
from ableton.v3.live import action, find_parent_track, liveobj_valid

from .mk4_log import get_logger
_logger = get_logger("session")


def get_clip_for_slot(slot):
    if liveobj_valid(slot):
        track = find_parent_track(slot)
        if track and track.has_midi_input:
            if slot.has_clip:
                clip = slot.clip
                return clip

            clip = create_sequencer_clip(track, slot=slot)
            return clip

        return None

    return None


class ClipSlotComponent(ClipSlotComponentBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.is_selecting = False

    def _on_launch_button_pressed(self):
        session = getattr(getattr(self, "parent", None), "parent", None)  # Scene -> Session
        slot = getattr(self, "_clip_slot", None)

        # Delete modifier: delete the real clip in this slot (if any), swallow launch.
        if getattr(session, "is_delete_modifier", False):
            if liveobj_valid(slot):
                has_clip = bool(getattr(slot, "has_clip", False))
                can_delete = hasattr(slot, "delete_clip")

                if has_clip and can_delete:
                    try:
                        slot.delete_clip()
                    except Exception as e:
                        _logger.exception("Exception during delete_clip(): %r", e)

            return

        if self.is_selecting:
            try:
                session.select_slot(slot)
            except Exception as e:
                _logger.exception("Exception in select_slot(): %r", e)
        else:
            super()._on_launch_button_pressed()

    def _feedback_value(self, track, slot_or_clip):
        value = super()._feedback_value(track, slot_or_clip)

        if self.is_selecting:
            try:
                parent_track = find_parent_track(slot_or_clip)
                is_midi = parent_track.has_midi_input if parent_track else False
            except Exception:
                parent_track = None
                is_midi = False

            has_clip = self._has_clip()
            controls_other = bool(getattr(slot_or_clip, "controls_other_clips", False))

            if has_clip or controls_other:
                value = "Session.SequencerClip" if is_midi else "Session.ClipStopped"
            else:
                value = "Session.SequencerSlot" if is_midi else "Session.Slot"

        # Check if we're in delete mode (only after is_selecting check to avoid interfering with sequencer)
        session = getattr(getattr(self, "parent", None), "parent", None)  # Scene -> Session
        is_delete_mode = getattr(session, "is_delete_modifier", False)
        
        if is_delete_mode:
            # In delete mode: show red for clips that can be deleted, OFF for empty slots
            slot = getattr(self, "_clip_slot", None)
            if liveobj_valid(slot):
                has_clip = bool(getattr(slot, "has_clip", False))
                can_delete = hasattr(slot, "delete_clip")
                if has_clip and can_delete:
                    return "Session.StopClip"  # Red, non-blinking
                else:
                    # Empty slot or can't delete - show OFF
                    return "Session.NoScene"  # OFF

        return value


class SessionComponent(SessionComponentBase):
    __events__ = ("clip_selected",)

    @depends(sequencer_clip=None)
    def __init__(self, sequencer_clip=None, *a, **k):
        super().__init__(*a, clip_slot_component_type=ClipSlotComponent, **k)
        self._sequencer_clip = sequencer_clip

        # Long-press Scene button arms this; pads delete while True.
        self.is_delete_modifier = False

    def set_delete_modifier(self, enabled: bool):
        self.is_delete_modifier = bool(enabled)
        # Update colors for all clip slots when delete mode changes
        self._update_clip_slot_colors()
    
    def _update_clip_slot_colors(self):
        """Update colors for all clip slots when delete mode changes."""
        # Get the buttons from control surface elements and call set_clip_launch_buttons
        # This is the same mechanism used by set_clip_select_buttons
        try:
            # Access control surface through canonical_parent
            control_surface = getattr(self, "canonical_parent", None)
            if control_surface and hasattr(control_surface, "elements"):
                elements = control_surface.elements
                if hasattr(elements, "main_pads"):
                    main_pads = elements.main_pads
                    # Call set_clip_launch_buttons with the buttons to trigger framework refresh
                    super().set_clip_launch_buttons(main_pads)
        except Exception as e:
            _logger.exception("SessionComponent._update_clip_slot_colors: exception: %r", e)

    def set_clip_select_buttons(self, buttons):
        is_selecting = bool(buttons)

        try:
            num_tracks = int(getattr(self._session_ring, "num_tracks", 0))
        except Exception:
            num_tracks = 0

        for si, scene in enumerate(getattr(self, "_scenes", []) or []):
            for x in range(num_tracks):
                try:
                    cs = scene.clip_slot(x)
                    cs.is_selecting = is_selecting
                except Exception as e:
                    _logger.exception(
                        "Exception setting is_selecting (scene=%s idx=%s): %r",
                        si,
                        x,
                        e,
                    )

        super().set_clip_launch_buttons(buttons)

    def select_slot(self, slot):
        try:
            clip = get_clip_for_slot(slot)
        except Exception as e:
            _logger.exception("Exception in get_clip_for_slot(): %r", e)
            clip = None

        try:
            self._sequencer_clip.set_clip(clip)
        except Exception as e:
            _logger.exception("Exception in sequencer_clip.set_clip(): %r", e)

        if clip:
            try:
                action.select(slot)
                self.notify_clip_selected()
            except Exception as e:
                _logger.exception("Exception during select/notify: %r", e)
