// ==========================================================
// RECOGNITION RULE
// Internal logic precedes interaction
// ==========================================================

use crate::entity::StringEntity;

pub struct MSDLSDRecognitionRule;

impl MSDLSDRecognitionRule {
    /// X-axis view (MSD)
    pub fn x_view(&self, entity: &StringEntity, depth: usize) -> usize {
        let bytes = entity.identity.as_bytes();

        if depth >= bytes.len() {
            0
        } else {
            (bytes[depth] as usize) + 1
        }
    }

    /// Y-axis view (LSD)
    pub fn y_view(&self, entity: &StringEntity, depth: usize) -> usize {
        let bytes = entity.identity.as_bytes();

        if bytes.is_empty() || depth >= bytes.len() {
            return 0;
        }

        let mirror_index = bytes.len() - 1 - depth;
        (bytes[mirror_index] as usize) + 1
    }

    /// Determines whether deeper recognition is possible.
    pub fn has_deeper_logic(
        &self,
        entity: &StringEntity,
        depth: usize,
    ) -> bool {
        depth < entity.identity.len()
    }
}