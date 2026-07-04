from abc import ABC, abstractmethod
from typing import Any, Tuple, Dict


# ----------------------------
# Entity
# ----------------------------
class Entity:
    def __init__(self, identity: int):
        self.identity = identity

    def internal_logic(self) -> Dict[str, Any]:
        """Entitet opisuje sam sebe kroz svoju internu logiku."""
        return {
            "binary": bin(self.identity)[2:],
            "digit_sum": sum(int(d) for d in str(self.identity)),
            "value": self.identity
        }

    def __repr__(self):
        return f"Entity({self.identity})"


# ----------------------------
# Recognition Rule (apstraktna baza)
# ----------------------------
class RecognitionRule(ABC):
    @abstractmethod
    def recognize(self, entity: Entity) -> Any:
        """Prepoznaje entitet i vraća njegovu poziciju u organizacionom prostoru."""
        pass


class BinaryRecognition(RecognitionRule):
    def recognize(self, entity: Entity) -> Tuple[int, str]:
        logic = entity.internal_logic()
        binary = logic["binary"]
        return (len(binary), binary)  # (broj bitova, binarni zapis)


class DigitSumRecognition(RecognitionRule):
    def recognize(self, entity: Entity) -> int:
        logic = entity.internal_logic()
        return logic["digit_sum"]


# ----------------------------
# Organization Space
# ----------------------------
class OrganizationSpace:
    def __init__(self):
        self.space: Dict[Any, list[Entity]] = {}

    def place(self, entity: Entity, position: Any):
        self.space.setdefault(position, []).append(entity)

    def show(self):
        for position in sorted(self.space):
            print(f"{position} → {self.space[position]}")


# ----------------------------
# Organization Engine
# ----------------------------
class OrganizationEngine:
    def __init__(self, rule: RecognitionRule):
        self.rule = rule

    def organize(self, entities: list[Entity]) -> OrganizationSpace:
        space = OrganizationSpace()
        for entity in entities:
            position = self.rule.recognize(entity)
            space.place(entity, position)
        return space


# ----------------------------
# Example / Test
# ----------------------------
if __name__ == "__main__":
    entities = [
        Entity(13), Entity(3), Entity(25),
        Entity(7), Entity(10), Entity(15)
    ]

    print("=== Binary Recognition ===")
    engine = OrganizationEngine(BinaryRecognition())
    space = engine.organize(entities)
    space.show()

    print("\n=== Digit Sum Recognition ===")
    engine = OrganizationEngine(DigitSumRecognition())
    space = engine.organize(entities)
    space.show()
