"""
Recognition Topology (3D) — revised conceptual prototype
========================================================

Axes:
    X — MSD Recognition   : the entity recognizes its own character at the
                            current recognition depth (front view).
    Y — LSD Recognition   : the entity recognizes its own character at the
                            mirrored depth (back view). Used by the
                            communication layer to classify conflicts.
    Z — Communication     : NOT a spatial coordinate. Z is a protocol.
                            When several entities recognize the same X room,
                            a CommunicationChannel opens between them and
                            coordinates a deeper recognition round.

Core claim preserved from the proposition:
    No pairwise comparison between entities is ever performed.
    This is enforced at runtime: StringEntity raises on any attempt
    to compare two entities.

Conflict model:
    - APPARENT conflict : entities share an X room but their LSD views or
      deeper logic differ → resolvable by deeper recognition.
      (The conflict came from a missing dimension, not from recognition.)
    - TRUE coexistence  : entities have identical identities → no depth
      will separate them; the channel closes and they coexist stably
      in arrival order (stability).

Run:  python3 recognition_3d.py        (self-test included)
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ==========================================================
# ENTITY — identity precedes organization
# ==========================================================
class StringEntity:

    def __init__(self, identity: str, index: int):
        self.identity = identity
        self.original_index = index

    # ---- no-comparison guard -----------------------------
    # The proposition forbids pairwise comparison. Enforce it.
    def _no_comparison(self, other):
        raise RuntimeError(
            "Pairwise comparison between entities is forbidden "
            "by the Recognition Organization proposition."
        )

    __lt__ = _no_comparison
    __le__ = _no_comparison
    __gt__ = _no_comparison
    __ge__ = _no_comparison

    def __repr__(self):
        return f"Entity({self.identity!r})"


# ==========================================================
# RECOGNITION RULE — internal logic precedes interaction
# ==========================================================
class MSDLSDRecognitionRule:
    """
    Recognition is introspective: the entity answers questions about
    itself. It never sees another entity.
    """

    # Room 0 is reserved for "my internal logic is exhausted at this
    # depth" — an exhausted entity naturally precedes all others,
    # which is a property of the entity itself, not a comparison.
    ROOM_COUNT = 257

    def x_view(self, entity: StringEntity, depth: int) -> int:
        """MSD recognition: which room do I belong to at this depth?"""
        s = entity.identity
        return 0 if depth >= len(s) else ord(s[depth]) + 1

    def y_view(self, entity: StringEntity, depth: int) -> int:
        """LSD recognition: my mirrored view at this depth."""
        s = entity.identity
        mirror = len(s) - 1 - depth
        return 0 if mirror < 0 else ord(s[mirror]) + 1

    def has_deeper_logic(self, entity: StringEntity, depth: int) -> bool:
        """Do I still carry unexpressed internal logic below this depth?"""
        return depth < len(entity.identity)


# ==========================================================
# COMMUNICATION CHANNEL — the Z axis as a protocol
# ==========================================================
@dataclass
class Announcement:
    """A message an entity sends into the channel about itself."""
    entity: StringEntity
    has_deeper: bool
    y_view: int


@dataclass
class CommunicationChannel:
    """
    Opens when several entities occupy the same X room.

    The channel never inspects two identities against each other.
    It only collects self-announcements and decides between:
      - coexistence (nobody has deeper logic → identical identities)
      - a deeper recognition round (someone still has internal logic)

    The Y (LSD) views let the channel classify the conflict as
    'apparent' (views differ → deeper recognition will resolve it)
    before recursing — conflict *prevention* insight, not resolution
    by comparison.
    """
    room: int
    depth: int
    log: List[str] = field(default_factory=list)

    def negotiate(self, entities: List[StringEntity], rule, engine):
        announcements = [
            Announcement(
                entity=e,
                has_deeper=rule.has_deeper_logic(e, self.depth),
                y_view=rule.y_view(e, self.depth),
            )
            for e in entities
        ]

        anyone_deeper = any(a.has_deeper for a in announcements)
        distinct_y = len({a.y_view for a in announcements}) > 1

        if not anyone_deeper:
            # TRUE coexistence: identities are exhausted and equal.
            self.log.append(
                f"depth={self.depth} room={self.room}: "
                f"{len(entities)} identical entities coexist (stable)"
            )
            return list(entities)  # arrival order preserved

        kind = "apparent (LSD views differ)" if distinct_y else "deep"
        self.log.append(
            f"depth={self.depth} room={self.room}: conflict is {kind}; "
            f"scheduling deeper recognition round"
        )
        # The channel does not order anyone. It adds the missing
        # dimension: one more level of self-recognition.
        return engine._organize_group(entities, self.depth + 1)


# ==========================================================
# ORGANIZATION ENGINE — orchestration, not judgement
# ==========================================================
class RecognitionTopologyEngine:

    def __init__(self, rule: Optional[MSDLSDRecognitionRule] = None):
        self.rule = rule or MSDLSDRecognitionRule()
        self.channel_logs: List[str] = []

    def organize(self, words: List[str]) -> List[str]:
        entities = [StringEntity(w, i) for i, w in enumerate(words)]
        self.channel_logs = []
        organized = self._organize_group(entities, depth=0)
        return [e.identity for e in organized]

    def _organize_group(self, entities: List[StringEntity], depth: int):
        # One recognition round: every entity places itself.
        rooms = {}
        for e in entities:
            x = self.rule.x_view(e, depth)
            rooms.setdefault(x, []).append(e)

        # Collect by walking the organization space itself
        # (rooms have fixed positions; nothing is compared).
        result = []
        for x in range(self.rule.ROOM_COUNT):
            occupants = rooms.get(x)
            if not occupants:
                continue
            if len(occupants) == 1:
                result.extend(occupants)
            else:
                # Z axis: open a communication channel for this room.
                channel = CommunicationChannel(room=x, depth=depth)
                result.extend(channel.negotiate(occupants, self.rule, self))
                self.channel_logs.extend(channel.log)
        return result


# ==========================================================
# SELF-TEST
# ==========================================================
if __name__ == "__main__":
    import random
    import string

    engine = RecognitionTopologyEngine()

    # 1) README example
    words = ["apple", "banana", "apricot", "cherry", "level", "radar"]
    got = engine.organize(words)
    print("engine :", got)
    print("sorted :", sorted(words))
    assert got == sorted(words), "README example mismatch"

    print("\nCommunication log:")
    for line in engine.channel_logs:
        print(" ", line)

    # 2) duplicates + prefixes (the hard cases)
    tricky = ["ab", "azb", "az", "ab", "", "a", "aab", "b"]
    assert engine.organize(tricky) == sorted(tricky), "tricky case mismatch"

    # 3) fuzz: 2000 random inputs
    random.seed(7)
    for _ in range(2000):
        ws = [
            "".join(random.choices(string.ascii_lowercase, k=random.randint(0, 8)))
            for _ in range(random.randint(0, 15))
        ]
        assert engine.organize(ws) == sorted(ws), f"fuzz mismatch: {ws}"

    # 4) no-comparison guard actually works
    try:
        StringEntity("a", 0) < StringEntity("b", 1)
        raise AssertionError("guard failed to trigger")
    except RuntimeError:
        pass

    print("\nAll tests passed: 2000 fuzz inputs match sorted(),")
    print("zero pairwise comparisons (guard enforced).")
