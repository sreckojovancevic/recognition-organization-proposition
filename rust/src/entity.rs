// ==========================================================
// ENTITY
// Identity precedes organization
// ==========================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StringEntity {
    pub identity: String,
    pub original_index: usize,
}

impl StringEntity {
    pub fn new(identity: &str, index: usize) -> Self {
        Self {
            identity: identity.to_string(),
            original_index: index,
        }
    }
}