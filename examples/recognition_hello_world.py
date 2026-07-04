#!/usr/bin/env python3
"""
Recognition Organization - Hello World

The simplest possible example:
Every number is its own identity.

Instead of comparing numbers (a > b),
each number recognizes itself through its internal geometry (bits).

This is the foundation of the entire Recognition Organization concept.
"""

from typing import List


class Entity:
    """An entity that knows its own identity."""
    
    def __init__(self, identity: int):
        self.identity = identity

    def get_bit(self, floor: int) -> int:
        """The entity itself says which bit it has on a given floor based on its geometry."""
        return (self.identity >> floor) & 1

    def __repr__(self):
        return str(self.identity)


class OrganizationSpace:
    """Minimal organization space: only rooms 0 and 1."""
    
    def __init__(self):
        # Fixed, minimal space: only rooms 0 and 1
        self.rooms = [[], []]

    def place(self, room_id: int, entity: Entity):
        self.rooms[room_id].append(entity)

    def collect(self) -> List[Entity]:
        return self.rooms[0] + self.rooms[1]


class RecognitionEngine:
    """
    Organizes integers (positive, negative, zero) without pairwise comparison.

    Metaphor:
      - Bits are the entity's geometry.
      - Floors are sieves through which entities fall.
      - The orchestrator measures the lowest point of the universe (offset / basement).
      - All entities are temporarily translated into positive space.
      - After falling through all floor sieves, entities are returned to their original world (offset restored).
    """
    
    def organize(self, values: List[int]) -> List[int]:
        """
        Sorts integers without pairwise compare.

        Metaphor:
          - Bits are the entity's geometry.
          - Floors are sieves through which entities fall.
          - The orchestrator measures the lowest point of the universe (offset / basement).
          - All entities are temporarily translated into positive space.
          - After falling through all floor sieves, entities are returned
            to their original world (offset restored).
        """
        if not values:
            return []
        
        # 1. Orchestrator measures the lowest point of the universe (potential basement)
        offset = min(values)
        
        # 2. Temporary translation of the environment into positive space
        translated_values = [v - offset for v in values]
        
        max_val = max(translated_values)
        total_floors = max_val.bit_length() if max_val > 0 else 1

        # Create entities with temporary geometry adjusted to the new environment
        entities = [Entity(v) for v in translated_values]

        # 3. Successive falling through floor sieves (orchestration flow)
        for floor in range(total_floors):
            space = OrganizationSpace()
            
            for entity in entities:
                room_id = entity.get_bit(floor)  # Entity decides its own room
                space.place(room_id, entity)
            
            entities = space.collect()            # Lift to the next level

        # 4. Return entities to their original world (offset restored)
        return [e.identity + offset for e in entities]


# ==================== ENVIRONMENT TESTING ====================
if __name__ == "__main__":
    engine = RecognitionEngine()
    
    # Test with a mix of positive, negative numbers, and zero
    numbers = [5, -3, 0, 8, -12, 2, -7, 1, 4, -6]
    
    print("Original chaos:", numbers)
    
    ordered_numbers = engine.organize(numbers)
    print("Self-organization:", ordered_numbers)
    
    # Verify it actually works
    expected = sorted(numbers)
    print(f"Matches sorted(): {ordered_numbers == expected}")
