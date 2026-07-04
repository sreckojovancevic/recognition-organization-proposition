"""
Semantic Recognition — conceptual prototype
===========================================

The first Recognition Rule whose behavior cannot be reduced to a
distribution sort. Entities are texts. There is no a-priori total
order over meanings — the output is not a sorted sequence but a
*semantic topology*: related texts end up in nearby rooms.

Mapping to the Recognition Organization framework:

    Entity            : a text
    Identity          : the content itself
    Internal Logic    : the entity's self-description as a term vector
                        (hashing trick — computed from the entity alone,
                        no corpus statistics, no other entity involved)
    Recognition Rule  : random hyperplane projection (LSH)
    Recognition       : the entity derives its room signature (bits)
                        from its own vector
    Organization Space: rooms addressed by signature prefixes
    Z / Communication : collision in a room opens a channel; the
                        channel adds resolution (more projection bits)
                        — a conflict is resolved by ADDING A DIMENSION,
                        never by comparing two entities

Note the LSH parallel: in locality-sensitive hashing, collisions are
routinely resolved by adding more hash bits — i.e., more dimensions.
The proposition's central insight ("a conflict may signal a missing
organizational dimension, not a recognition error") is the literal
mechanics of LSH.

Coexistence here is *rule-relative*: two texts that share the full
signature are semantically indistinguishable under this rule and
coexist stably. A finer rule might separate them. Identity of position
is not identity of identity.

No pairwise comparison between entities is performed — enforced at
runtime by a guard on TextEntity.

Run:  python3 recognition_semantic.py       (self-test included)
"""

import hashlib
import math
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ==========================================================
# ENTITY — identity precedes organization
# ==========================================================
class TextEntity:

    def __init__(self, identity: str, index: int, topic: str = "?"):
        self.identity = identity
        self.original_index = index
        self.topic = topic          # ground-truth label, used only by tests

    def internal_logic(self) -> Dict[int, float]:
        """
        The entity describes itself: a signed term-frequency vector via
        the hashing trick. Computed from the identity alone — Axiom 3:
        recognition uses internal information.
        """
        vector: Dict[int, float] = {}
        for token in re.findall(r"[a-z0-9]+", self.identity.lower()):
            digest = hashlib.md5(token.encode()).digest()
            dim = int.from_bytes(digest[:4], "big") % SemanticRecognitionRule.DIMS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[dim] = vector.get(dim, 0.0) + sign
        norm = math.sqrt(sum(v * v for v in vector.values()))
        if norm > 0:
            vector = {d: v / norm for d, v in vector.items()}
        return vector

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
        return f"Entity({self.identity[:32]!r})"


# ==========================================================
# RECOGNITION RULE — random hyperplane projection (LSH)
# ==========================================================
class SemanticRecognitionRule:

    DIMS = 512          # dimensionality of the self-description space
    MAX_BITS = 32       # maximum signature resolution
    BASE_BITS = 4       # resolution of the initial recognition round
    STEP_BITS = 2       # resolution added per communication round

    def __init__(self, seed: int = 11):
        rng = random.Random(seed)
        # MAX_BITS hyperplanes; each recognition bit answers one
        # introspective question: "on which side of this plane am I?"
        self.planes: List[Dict[int, float]] = []
        for _ in range(self.MAX_BITS):
            self.planes.append(
                {d: rng.gauss(0.0, 1.0) for d in range(self.DIMS)}
            )

    def signature(self, entity: TextEntity, bits: int) -> Tuple[int, ...]:
        """The entity derives its own room address. No other entity involved."""
        vector = entity.internal_logic()
        sig = []
        for plane in self.planes[:bits]:
            projection = sum(weight * plane[dim] for dim, weight in vector.items())
            sig.append(1 if projection >= 0.0 else 0)
        return tuple(sig)

    def has_deeper_logic(self, entity: TextEntity, bits: int) -> bool:
        """Can this entity express itself at a finer resolution?"""
        return bits < self.MAX_BITS and len(entity.internal_logic()) > 0


# ==========================================================
# COMMUNICATION CHANNEL — the Z axis as a protocol
# ==========================================================
@dataclass
class CommunicationChannel:
    room: Tuple[int, ...]
    bits: int
    log: List[str] = field(default_factory=list)

    def negotiate(self, entities: List[TextEntity], rule, engine):
        anyone_deeper = any(
            rule.has_deeper_logic(e, self.bits) for e in entities
        )
        if not anyone_deeper:
            # Rule-relative coexistence: indistinguishable under this
            # rule at full resolution. A different rule might separate
            # them — identity of position is not identity of identity.
            self.log.append(
                f"bits={self.bits}: {len(entities)} entities coexist "
                f"(semantically indistinguishable under this rule)"
            )
            return list(entities)

        self.log.append(
            f"bits={self.bits}: conflict in room {''.join(map(str, self.room))} "
            f"→ adding resolution (missing dimension), not comparing"
        )
        return engine._organize_group(
            entities, min(self.bits + rule.STEP_BITS, rule.MAX_BITS)
        )


# ==========================================================
# ORGANIZATION ENGINE — orchestration, not judgement
# ==========================================================
class SemanticOrganizationEngine:

    def __init__(self, rule: SemanticRecognitionRule = None):
        self.rule = rule or SemanticRecognitionRule()
        self.channel_logs: List[str] = []

    def organize(self, texts: List[str], topics: List[str] = None) -> List[TextEntity]:
        topics = topics or ["?"] * len(texts)
        entities = [
            TextEntity(t, i, topic) for i, (t, topic) in enumerate(zip(texts, topics))
        ]
        self.channel_logs = []
        return self._organize_group(entities, self.rule.BASE_BITS)

    def _organize_group(self, entities: List[TextEntity], bits: int):
        rooms: Dict[Tuple[int, ...], List[TextEntity]] = {}
        for e in entities:
            rooms.setdefault(self.rule.signature(e, bits), []).append(e)

        # Walk the space by room address (positions are compared,
        # entities never are).
        result = []
        for address in sorted(rooms):
            occupants = rooms[address]
            if len(occupants) == 1 or bits >= self.rule.MAX_BITS:
                if len(occupants) > 1:
                    channel = CommunicationChannel(address, bits)
                    occupants = channel.negotiate(occupants, self.rule, self)
                    self.channel_logs.extend(channel.log)
                result.extend(occupants)
            else:
                channel = CommunicationChannel(address, bits)
                result.extend(channel.negotiate(occupants, self.rule, self))
                self.channel_logs.extend(channel.log)
        return result


# ==========================================================
# SELF-TEST
# ==========================================================
if __name__ == "__main__":

    corpus = [
        # animals
        ("the cat chased the mouse across the kitchen floor", "animals"),
        ("a dog barked at the cat near the garden fence", "animals"),
        ("the mouse escaped from the cat into a small hole", "animals"),
        ("wild dogs hunt in packs while cats hunt alone", "animals"),
        # programming
        ("the python function returns a sorted list of values", "code"),
        ("a recursive function calls itself until the base case", "code"),
        ("the compiler reports an error in the main function", "code"),
        ("unit tests verify that every function returns correct values", "code"),
        # cooking
        ("simmer the tomato sauce with garlic and fresh basil", "food"),
        ("bake the bread until the crust turns golden brown", "food"),
        ("add garlic and olive oil to the tomato pasta sauce", "food"),
        ("knead the dough and let the bread rise before baking", "food"),
        # duplicates — must coexist
        ("the cat chased the mouse across the kitchen floor", "animals"),
    ]
    texts = [t for t, _ in corpus]
    topics = [c for _, c in corpus]

    rule = SemanticRecognitionRule()
    engine = SemanticOrganizationEngine(rule)
    organized = engine.organize(texts, topics)

    print("=== Semantic organization (final neighborhood order) ===")
    for e in organized:
        sig = "".join(map(str, rule.signature(e, 8)))
        print(f"  [{sig}] ({e.topic:7s}) {e.identity}")

    print("\n=== Communication log ===")
    for line in engine.channel_logs:
        print(" ", line)

    # ---- Test 1: semantic locality --------------------------------
    # Intra-topic signature agreement must exceed inter-topic agreement.
    def agreement(a: TextEntity, b: TextEntity) -> int:
        sa, sb = rule.signature(a, rule.MAX_BITS), rule.signature(b, rule.MAX_BITS)
        return sum(1 for x, y in zip(sa, sb) if x == y)

    ents = [TextEntity(t, i, c) for i, (t, c) in enumerate(corpus[:12])]
    intra, inter = [], []
    for i in range(len(ents)):
        for j in range(i + 1, len(ents)):
            (intra if ents[i].topic == ents[j].topic else inter).append(
                agreement(ents[i], ents[j])
            )
    mean_intra = sum(intra) / len(intra)
    mean_inter = sum(inter) / len(inter)
    print(f"\nintra-topic bit agreement : {mean_intra:.1f}/{rule.MAX_BITS}")
    print(f"inter-topic bit agreement : {mean_inter:.1f}/{rule.MAX_BITS}")
    assert mean_intra > mean_inter, "semantic locality not achieved"

    # ---- Test 2: duplicates coexist --------------------------------
    dup_positions = [
        k for k, e in enumerate(organized)
        if e.identity == "the cat chased the mouse across the kitchen floor"
    ]
    assert len(dup_positions) == 2
    assert dup_positions[1] == dup_positions[0] + 1, "duplicates must coexist adjacently"
    first, second = organized[dup_positions[0]], organized[dup_positions[1]]
    assert first.original_index < second.original_index, "coexistence must be stable"

    # ---- Test 3: rule pluralism ------------------------------------
    # The same identities under a different rule occupy different
    # positions: organization is rule-relative.
    other = SemanticRecognitionRule(seed=99)
    moved = sum(
        1 for e in ents
        if rule.signature(e, 8) != other.signature(e, 8)
    )
    print(f"\nrule pluralism: {moved}/{len(ents)} entities occupy a different "
          f"room under a different rule")
    assert moved > 0

    # ---- Test 4: no-comparison guard -------------------------------
    try:
        TextEntity("a", 0) < TextEntity("b", 1)
        raise AssertionError("guard failed to trigger")
    except RuntimeError:
        pass

    print("\nAll tests passed: semantic locality achieved, duplicates coexist")
    print("stably, organization is rule-relative, zero pairwise comparisons.")
