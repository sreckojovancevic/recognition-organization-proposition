// ==========================================================
// ORGANIZATION ENGINE
// Orchestration, not judgement
// ==========================================================

use std::collections::BTreeMap;

use crate::channel::CommunicationChannel;
use crate::entity::StringEntity;
use crate::recognition::MSDLSDRecognitionRule;

pub struct RecognitionTopologyEngine {
    pub channel_logs: Vec<String>,
}

impl RecognitionTopologyEngine {
    pub fn new() -> Self {
        Self {
            channel_logs: Vec::new(),
        }
    }

    pub fn organize(&mut self, words: &[&str]) -> Vec<String> {
        self.channel_logs.clear();

        let rule = MSDLSDRecognitionRule;

        let entities: Vec<StringEntity> = words
            .iter()
            .enumerate()
            .map(|(i, &w)| StringEntity::new(w, i))
            .collect();

        let organized = self.organize_group(
            entities,
            0,
            &rule,
        );

        organized
            .into_iter()
            .map(|e| e.identity)
            .collect()
    }

    pub(crate) fn organize_group(
        &mut self,
        entities: Vec<StringEntity>,
        depth: usize,
        rule: &MSDLSDRecognitionRule,
    ) -> Vec<StringEntity> {

        let mut rooms: BTreeMap<usize, Vec<StringEntity>> =
            BTreeMap::new();

        for entity in entities {

            let room = rule.x_view(&entity, depth);

            rooms
                .entry(room)
                .or_insert_with(Vec::new)
                .push(entity);
        }

        let mut result = Vec::new();

        for (room, occupants) in rooms {

            if occupants.len() == 1 {

                result.push(occupants[0].clone());

            } else {

                let channel =
                    CommunicationChannel::new(room, depth);

                let organized =
                    channel.negotiate(
                        occupants,
                        rule,
                        self,
                    );

                result.extend(organized);
            }
        }

        result
    }
}