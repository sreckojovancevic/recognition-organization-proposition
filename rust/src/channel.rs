// ==========================================================
// COMMUNICATION CHANNEL
// The Z axis as a protocol
// ==========================================================

use crate::entity::StringEntity;
use crate::engine::RecognitionTopologyEngine;
use crate::recognition::MSDLSDRecognitionRule;

pub struct CommunicationChannel {
    pub room: usize,
    pub depth: usize,
}

impl CommunicationChannel {
    pub fn new(room: usize, depth: usize) -> Self {
        Self { room, depth }
    }

    pub fn negotiate(
        &self,
        entities: Vec<StringEntity>,
        rule: &MSDLSDRecognitionRule,
        engine: &mut RecognitionTopologyEngine,
    ) -> Vec<StringEntity> {

        let announcements: Vec<_> = entities
            .iter()
            .map(|e| {
                let has_deeper = rule.has_deeper_logic(e, self.depth);
                let y_view = rule.y_view(e, self.depth);

                (e.clone(), has_deeper, y_view)
            })
            .collect();

        let anyone_deeper = announcements
            .iter()
            .any(|(_, deeper, _)| *deeper);

        let first_y = announcements[0].2;

        let distinct_y = announcements
            .iter()
            .any(|(_, _, y)| *y != first_y);

        if !anyone_deeper {

            engine.channel_logs.push(format!(
                "depth={} room={}: {} identical entities coexist (stable)",
                self.depth,
                self.room,
                entities.len()
            ));

            return entities;
        }

        let conflict_type = if distinct_y {
            "apparent (LSD views differ)"
        } else {
            "deep"
        };

        engine.channel_logs.push(format!(
            "depth={} room={}: conflict is {}; scheduling deeper recognition round",
            self.depth,
            self.room,
            conflict_type
        ));

        engine.organize_group(
            entities,
            self.depth + 1,
            rule,
        )
    }
}