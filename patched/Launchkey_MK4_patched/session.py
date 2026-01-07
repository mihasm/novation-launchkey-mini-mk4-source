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
        _logger.debug(
            "get_clip_for_slot: slot=%s liveobj_valid=True track=%s has_midi_input=%s has_clip=%s",
            slot,
            track,
            getattr(track, "has_midi_input", None) if track else None,
            getattr(slot, "has_clip", None),
        )
        if track and track.has_midi_input:
            if slot.has_clip:
                clip = slot.clip
                _logger.debug("get_clip_for_slot: returning real clip=%s", clip)
                return clip

            clip = create_sequencer_clip(track, slot=slot)
            _logger.debug("get_clip_for_slot: created sequencer_clip=%s", clip)
            return clip

        _logger.debug("get_clip_for_slot: not midi track -> None")
        return None

    _logger.debug("get_clip_for_slot: slot invalid -> None (slot=%s)", slot)
    return None


class ClipSlotComponent(ClipSlotComponentBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.is_selecting = False
        _logger.debug("ClipSlotComponent.__init__: self=%s parent=%s", self, getattr(self, "parent", None))

    def _on_launch_button_pressed(self):
        session = getattr(getattr(self, "parent", None), "parent", None)  # Scene -> Session
        slot = getattr(self, "_clip_slot", None)

        _logger.debug(
            "ClipSlotComponent._on_launch_button_pressed: self=%s session=%s is_selecting=%s delete_modifier=%s slot=%s",
            self,
            session,
            self.is_selecting,
            getattr(session, "is_delete_modifier", None),
            slot,
        )

        # Delete modifier: delete the real clip in this slot (if any), swallow launch.
        if getattr(session, "is_delete_modifier", False):
            if liveobj_valid(slot):
                has_clip = bool(getattr(slot, "has_clip", False))
                can_delete = hasattr(slot, "delete_clip")
                _logger.debug(
                    "Delete branch: slot valid; has_clip=%s has delete_clip=%s",
                    has_clip,
                    can_delete,
                )

                if has_clip and can_delete:
                    try:
                        _logger.debug("Delete branch: calling slot.delete_clip() on %s", slot)
                        slot.delete_clip()
                        _logger.debug("Delete branch: delete_clip() done")
                    except Exception as e:
                        _logger.exception("Delete branch: exception during delete_clip(): %r", e)
                else:
                    _logger.debug("Delete branch: nothing to delete (has_clip=%s can_delete=%s)", has_clip, can_delete)
            else:
                _logger.debug("Delete branch: slot invalid -> nothing to do")

            _logger.debug("Delete branch: swallowing launch (return)")
            return

        if self.is_selecting:
            _logger.debug("Selecting branch: calling session.select_slot(slot=%s)", slot)
            try:
                session.select_slot(slot)
            except Exception as e:
                _logger.exception("Selecting branch: exception in select_slot(): %r", e)
        else:
            _logger.debug("Default branch: delegating to super()._on_launch_button_pressed()")
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

            _logger.debug(
                "ClipSlotComponent._feedback_value: selecting=True track=%s slot_or_clip=%s parent_track=%s "
                "is_midi=%s _has_clip=%s controls_other=%s base_value=%r",
                track,
                slot_or_clip,
                parent_track,
                is_midi,
                has_clip,
                controls_other,
                value,
            )

            if has_clip or controls_other:
                value = "Session.SequencerClip" if is_midi else "Session.ClipStopped"
            else:
                value = "Session.SequencerSlot" if is_midi else "Session.Slot"

            _logger.debug("ClipSlotComponent._feedback_value: overridden_value=%r", value)

        return value


class SessionComponent(SessionComponentBase):
    __events__ = ("clip_selected",)

    @depends(sequencer_clip=None)
    def __init__(self, sequencer_clip=None, *a, **k):
        _logger.debug("SessionComponent.__init__: entering; sequencer_clip=%s a=%s k_keys=%s", sequencer_clip, a, list(k.keys()))
        super().__init__(*a, clip_slot_component_type=ClipSlotComponent, **k)
        self._sequencer_clip = sequencer_clip

        # Long-press Scene button arms this; pads delete while True.
        self.is_delete_modifier = False

        _logger.debug(
            "SessionComponent.__init__: done; self=%s scenes=%s session_ring=%s num_tracks=%s",
            self,
            len(getattr(self, "_scenes", []) or []),
            getattr(self, "_session_ring", None),
            getattr(getattr(self, "_session_ring", None), "num_tracks", None),
        )

    def set_delete_modifier(self, enabled: bool):
        prev = getattr(self, "is_delete_modifier", None)
        self.is_delete_modifier = bool(enabled)
        _logger.debug("SessionComponent.set_delete_modifier: %s -> %s", prev, self.is_delete_modifier)

    def set_clip_select_buttons(self, buttons):
        is_selecting = bool(buttons)
        _logger.debug(
            "SessionComponent.set_clip_select_buttons: buttons=%s is_selecting=%s scenes=%s",
            buttons,
            is_selecting,
            len(getattr(self, "_scenes", []) or []),
        )

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
                        "SessionComponent.set_clip_select_buttons: exception setting is_selecting (scene=%s idx=%s): %r",
                        si,
                        x,
                        e,
                    )

        _logger.debug("SessionComponent.set_clip_select_buttons: delegating to super().set_clip_launch_buttons(buttons)")
        super().set_clip_launch_buttons(buttons)

    def select_slot(self, slot):
        _logger.debug("SessionComponent.select_slot: slot=%s valid=%s", slot, liveobj_valid(slot))
        try:
            clip = get_clip_for_slot(slot)
        except Exception as e:
            _logger.exception("SessionComponent.select_slot: exception in get_clip_for_slot(): %r", e)
            clip = None

        _logger.debug("SessionComponent.select_slot: resolved clip=%s", clip)

        try:
            self._sequencer_clip.set_clip(clip)
            _logger.debug("SessionComponent.select_slot: sequencer_clip.set_clip(%s) done", clip)
        except Exception as e:
            _logger.exception("SessionComponent.select_slot: exception in sequencer_clip.set_clip(): %r", e)

        if clip:
            try:
                _logger.debug("SessionComponent.select_slot: action.select(slot=%s)", slot)
                action.select(slot)
                _logger.debug("SessionComponent.select_slot: action.select done; notifying clip_selected")
                self.notify_clip_selected()
            except Exception as e:
                _logger.exception("SessionComponent.select_slot: exception during select/notify: %r", e)
        else:
            _logger.debug("SessionComponent.select_slot: no clip -> not selecting/notifying")
