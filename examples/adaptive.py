"""
Adaptive Recognition — conceptual prototype
===========================================

Introduces a new class of rules into ℛ: **adaptive rules**.

    Static rule    : Rr exists before the data. Recognition is purely
                     introspective (recognition_3d, recognition_semantic,
                     BitLengthRule below).
    Adaptive rule  : the rule is CALIBRATED from the population it is
                     about to organize (here: log-scale interpolation
                     over [min, max]). The organization space adapts to
                     the universe; recognition itself remains
                     introspective — the entity still only asks
                     questions about itself against the calibrated rule.

Honesty note (important):
    Calibration aggregates population statistics (min, max, count).
    Computing those statistics compares *announced values*, never
    entities — but it IS comparison, and pretending otherwise would be
    comparison through the back door. Adaptive rules therefore relax
    the framework's purity at CALIBRATION time while preserving it at
    ORGANIZATION time. The static BitLengthRule is included as the
    purity baseline: logarithmic rooms with no calibration at all
    (bit_length = position of the highest bit = ⌊log₂⌋ + 1, derived
    by the entity from itself alone).

Conflict model (the part that makes it work):
    A collision in a room opens a CommunicationChannel. The channel
    RECALIBRATES the rule over that room's population only — the space
    refines itself exactly where the conflict density is highest.
    Local recalibration is the adaptive form of "adding a missing
    dimension": the room becomes its own, finer universe.
    Termination is guaranteed: after recalibration the local minimum
    and maximum always land in different rooms, so every round makes
    strict progress until only identical values remain — and identical
    values coexist stably (arrival order).

No pairwise comparison between entities is performed — enforced at
runtime by a guard on NumberEntity.

Run:  python3 recognition_adaptive.py       (self-test included)
"""

import math
from dataclasses import dataclass, field
from typing import List


# ==========================================================
# ENTITY — identity precedes organization
# ==========================================================
class NumberEntity:

    def __init__(self, identity: float, index: int):
        self.identity = identity
        self.original_index = index

    def announce(self) -> float:
        """Self-description sent to the space for calibration."""
        return self.identity

    # ---- no-comparison guard -----------------------------
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
        return f"Entity({self.identity})"


# ==========================================================
# ADAPTIVE RULE — calibrated from the population
# ==========================================================
class AdaptiveLogRule:
    """
    Logarithmic interpolation over the announced range of the
    population. Log scale keeps the rule useful when identities span
    several orders of magnitude.
    """

    def __init__(self, announcements: List[float]):
        self.lo, self.hi = min(announcements), max(announcements)  # calibration
        self.room_count = len(announcements)
        self.shift = 1.0 - self.lo if self.lo <= 0 else 0.0
        log_lo = math.log(self.lo + self.shift)
        log_hi = math.log(self.hi + self.shift)
        span = log_hi - log_lo
        self.scale = (self.room_count - 1) / span if span > 0 else 0.0
        self.log_lo = log_lo

    def recognize(self, entity: NumberEntity) -> int:
        """
        Introspective: the entity places itself using the calibrated map.

        The first two checks are identity recognition, not comparison:
        "am I the calibrated boundary of this universe?" (equality).
        They guarantee that every recalibration round makes strict
        progress — floating-point rounding of the interpolation could
        otherwise map the maximum below the last room and stall the
        refinement forever.
        """
        if entity.identity == self.hi:
            return self.room_count - 1
        if entity.identity == self.lo:
            return 0
        log_val = math.log(entity.identity + self.shift)
        room = int((log_val - self.log_lo) * self.scale)
        return max(0, min(room, self.room_count - 1))


# ==========================================================
# COMMUNICATION CHANNEL — local recalibration as the Z axis
# ==========================================================
@dataclass
class CommunicationChannel:
    room: int
    log: List[str] = field(default_factory=list)

    def negotiate(self, entities: List[NumberEntity], engine):
        announcements = [e.announce() for e in entities]

        if len(set(announcements)) == 1:
            # True coexistence: identical identities. Stable, arrival order.
            self.log.append(
                f"room={self.room}: {len(entities)} identical entities "
                f"coexist (stable)"
            )
            return list(entities)

        # Apparent conflict: the room becomes its own finer universe.
        self.log.append(
            f"room={self.room}: conflict → recalibrating a local space "
            f"over {len(entities)} entities (adding a missing dimension)"
        )
        return engine._organize_group(entities)


# ==========================================================
# ORGANIZATION ENGINE — orchestration, not judgement
# ==========================================================
class AdaptiveOrganizationEngine:

    def __init__(self):
        self.channel_logs: List[str] = []
        self.recalibrations = 0

    def organize(self, values: List[float]) -> List[float]:
        entities = [NumberEntity(v, i) for i, v in enumerate(values)]
        self.channel_logs = []
        self.recalibrations = 0
        if not entities:
            return []
        return [e.identity for e in self._organize_group(entities)]

    def _organize_group(self, entities: List[NumberEntity]):
        # Calibrate a rule for THIS population.
        rule = AdaptiveLogRule([e.announce() for e in entities])
        self.recalibrations += 1

        rooms = {}
        for e in entities:
            rooms.setdefault(rule.recognize(e), []).append(e)

        # Walk the space by room index (positions, never entities).
        result = []
        for room in range(rule.room_count):
            occupants = rooms.get(room)
            if not occupants:
                continue
            if len(occupants) == 1:
                result.extend(occupants)
            else:
                channel = CommunicationChannel(room)
                result.extend(channel.negotiate(occupants, self))
                self.channel_logs.extend(channel.log)
        return result


# ==========================================================
# STATIC BASELINE — BitLengthRule (no calibration, pure introspection)
# ==========================================================
class BitLengthOrganizationEngine:
    """
    The purity baseline: logarithmic rooms with zero calibration.
    Room = bit_length (position of the entity's own highest bit);
    deeper rounds recognize successive bits below the MSB. Entities
    in the same room share bit_length, so bit positions stay aligned.
    Non-negative integers only.
    """

    MAX_ROOMS = 65  # bit_lengths 0..64

    def organize(self, values: List[int]) -> List[int]:
        entities = [NumberEntity(v, i) for i, v in enumerate(values)]
        return [e.identity for e in self._organize_group(entities, depth=-1)]

    def _organize_group(self, entities, depth):
        rooms = {}
        for e in entities:
            if depth == -1:
                room = e.identity.bit_length()          # ⌊log₂⌋ + 1
            else:
                pos = e.identity.bit_length() - 2 - depth
                room = (e.identity >> pos) & 1 if pos >= 0 else 0
            rooms.setdefault(room, []).append(e)

        result = []
        for room in range(self.MAX_ROOMS):
            occupants = rooms.get(room)
            if not occupants:
                continue
            if len(occupants) == 1 or len({e.identity for e in occupants}) == 1:
                result.extend(occupants)                # alone or identical
            else:
                result.extend(self._organize_group(occupants, depth + 1))
        return result


# ==========================================================
# SELF-TEST
# ==========================================================
if __name__ == "__main__":
    import random

    engine = AdaptiveOrganizationEngine()

    # 1) the original example
    data = [10, 100000, 50, 100, 500, 2000]
    got = engine.organize(data)
    print("input     :", data)
    print("organized :", got)
    assert got == sorted(data)

    # 2) adversarial arrival order — the case the raw prototype missed
    tricky = [50, 10, 2000, 500, 100000, 100]
    assert engine.organize(tricky) == sorted(tricky), "arrival-order case failed"
    print("\nCommunication log (adversarial input):")
    for line in engine.channel_logs:
        print(" ", line)
    print(f"local recalibrations: {engine.recalibrations}")

    # 3) fuzz: negatives, zeros, duplicates, wide ranges
    random.seed(3)
    for _ in range(1000):
        n = random.randint(0, 40)
        vals = [random.randint(-10**6, 10**6) for _ in range(n)]
        assert engine.organize(vals) == sorted(vals), f"fuzz failed: {vals}"

    # 4) stability: equal values keep arrival order
    ents = [NumberEntity(7, 0), NumberEntity(7, 1), NumberEntity(7, 2)]
    out = AdaptiveOrganizationEngine()._organize_group(ents)
    assert [e.original_index for e in out] == [0, 1, 2], "coexistence must be stable"

    # 5) static baseline: BitLengthRule, zero calibration
    bit_engine = BitLengthOrganizationEngine()
    for _ in range(1000):
        vals = [random.randint(0, 10**9) for _ in range(random.randint(0, 40))]
        assert bit_engine.organize(vals) == sorted(vals), "bit-length baseline failed"

    # 6) no-comparison guard
    try:
        NumberEntity(1, 0) < NumberEntity(2, 1)
        raise AssertionError("guard failed to trigger")
    except RuntimeError:
        pass

    print("\nAll tests passed: adaptive rule matches sorted() on 1000 fuzz")
    print("inputs (incl. negatives/duplicates), arrival order is irrelevant,")
    print("coexistence is stable, static bit-length baseline verified,")
    print("zero pairwise comparisons between entities.")
