use std::collections::BTreeMap;
use std::time::{Duration, Instant};
use rand::Rng;

// =========================================================================
// STRUKTURE (Ostaju 100% netaknute)
// =========================================================================
#[derive(Debug, Clone)]
pub struct StringEntity {
    pub id: String,
    pub room_id: u8,
    pub conflict_level: u8,
    #[allow(dead_code)]
    pub payload: String,
}

#[derive(Debug)]
pub struct AuditLog {
    #[allow(dead_code)]
    pub message: String,
}

// =========================================================================
// ORIGINALNA TOPOLOGIJA (sa BTreeMap i logovima)
// =========================================================================
pub fn topology_original(elements: &[StringEntity]) -> (Vec<StringEntity>, Vec<AuditLog>) {
    let mut rooms: BTreeMap<usize, Vec<StringEntity>> = BTreeMap::new();
    let mut logs = Vec::new();

    for e in elements {
        rooms.entry(e.room_id as usize).or_default().push(e.clone());
    }

    let mut result = Vec::with_capacity(elements.len());
    for (room_id, mut group) in rooms {
        group.sort_by(|a, b| a.conflict_level.cmp(&b.conflict_level));

        for e in &group {
            logs.push(AuditLog {
                message: format!("Entity {} negotiated in room {} at level {}", e.id, room_id, e.conflict_level),
            });
            result.push(e.clone());
        }
    }

    (result, logs)
}

// =========================================================================
// VARIJANTA 1: FAST BUCKET - LAZY ALLOCATION (Sa Vec::new())
// =========================================================================
pub fn topology_fast_bucket_lazy(elements: &[StringEntity]) -> Vec<StringEntity> {
    // Počinje sa 0 bajtova na heap-u, alocira se lenjo (kako elementi pristižu)
    let mut grid: [[Vec<usize>; 8]; 256] = std::array::from_fn(|_| std::array::from_fn(|_| Vec::new()));

    for (idx, entity) in elements.iter().enumerate() {
        let room = entity.room_id as usize;
        let level = entity.conflict_level as usize;
        if level < 8 {
            grid[room][level].push(idx);
        }
    }

    let mut sorted_result = Vec::with_capacity(elements.len());
    for room in 0..256 {
        for level in 0..8 {
            for &original_idx in &grid[room][level] {
                sorted_result.push(elements[original_idx].clone());
            }
        }
    }

    sorted_result
}

// =========================================================================
// VARIJANTA 2: FAST BUCKET - PRE-ALLOCATION (Sa with_capacity)
// =========================================================================
pub fn topology_fast_bucket_prealloc(elements: &[StringEntity]) -> Vec<StringEntity> {
    // Unapred računamo prosečan kapacitet i odmah zauzimamo memoriju
    let estimated_capacity = (elements.len() / 2048) + 4;
    let mut grid: [[Vec<usize>; 8]; 256] = std::array::from_fn(|_| {
        std::array::from_fn(|_| Vec::with_capacity(estimated_capacity))
    });

    for (idx, entity) in elements.iter().enumerate() {
        let room = entity.room_id as usize;
        let level = entity.conflict_level as usize;
        if level < 8 {
            grid[room][level].push(idx);
        }
    }

    let mut sorted_result = Vec::with_capacity(elements.len());
    for room in 0..256 {
        for level in 0..8 {
            for &original_idx in &grid[room][level] {
                sorted_result.push(elements[original_idx].clone());
            }
        }
    }

    sorted_result
}

// =========================================================================
// FORMATIRANJE VREMENA
// =========================================================================
fn format_duration(d: Duration) -> String {
    if d.as_secs() > 0 {
        format!("{:.2} s", d.as_secs_f64())
    } else if d.as_millis() > 0 {
        format!("{:.2} ms", d.as_nanos() as f64 / 1_000_000.0)
    } else {
        format!("{:.2} µs", d.as_nanos() as f64 / 1_000.0)
    }
}

// =========================================================================
// PROŠIRENI BENCHMARK
// =========================================================================
pub fn main() {
    let sizes = vec![1_000, 10_000, 50_000, 100_000];
    let mut rng = rand::thread_rng();

    println!("=========================================================================================================================");
    println!(" {:<12} | {:<15} | {:<26} | {:<25} | {:<25}", "Elements", "Standard Sort", "Topologija (Sa Logovima)", "Fast Bucket (Lazy)", "Fast Bucket (Prealloc)");
    println!("=========================================================================================================================");

    for size in sizes {
        let mock_elements: Vec<StringEntity> = (0..size)
            .map(|i| StringEntity {
                id: format!("UUID-{}", i),
                room_id: rng.gen_range(0..256) as u8,
                conflict_level: rng.gen_range(0..8) as u8,
                payload: "Data packet payload string content".to_string(),
            })
            .collect();

        // 1. Standardni Sort
        let mut std_data = mock_elements.clone();
        let start_std = Instant::now();
        std_data.sort_by(|a, b| {
            let room_cmp = a.room_id.cmp(&b.room_id);
            if room_cmp == std::cmp::Ordering::Equal {
                a.conflict_level.cmp(&b.conflict_level)
            } else {
                room_cmp
            }
        });
        let duration_std = start_std.elapsed();

        // 2. Originalna Topologija sa logovima
        let start_orig = Instant::now();
        let (res_orig, logs_orig) = topology_original(&mock_elements);
        let duration_orig = start_orig.elapsed();

        // 3. Fast Bucket - Lazy
        let start_lazy = Instant::now();
        let res_lazy = topology_fast_bucket_lazy(&mock_elements);
        let duration_lazy = start_lazy.elapsed();

        // 4. Fast Bucket - Prealloc
        let start_prealloc = Instant::now();
        let res_prealloc = topology_fast_bucket_prealloc(&mock_elements);
        let duration_prealloc = start_prealloc.elapsed();

        // Rigorozne provere ispravnosti za sve tri varijante
        assert_eq!(res_orig.len(), mock_elements.len());
        assert_eq!(res_lazy.len(), mock_elements.len());
        assert_eq!(res_prealloc.len(), mock_elements.len());

        let mut sorted_orig = res_orig.iter().map(|e| e.id.clone()).collect::<Vec<_>>();
        let mut sorted_lazy = res_lazy.iter().map(|e| e.id.clone()).collect::<Vec<_>>();
        let mut sorted_prealloc = res_prealloc.iter().map(|e| e.id.clone()).collect::<Vec<_>>();
        
        sorted_orig.sort();
        sorted_lazy.sort();
        sorted_prealloc.sort();
        
        assert_eq!(sorted_orig, sorted_lazy);
        assert_eq!(sorted_orig, sorted_prealloc);

        let _log_count = logs_orig.len();

        // Ispis proširene tabele
        println!(
            " {:<12} | {:<15} | {:<26} | {:<25} | {:<25}",
            format!("{:#}", size),
            format_duration(duration_std),
            format_duration(duration_orig),
            format_duration(duration_lazy),
            format_duration(duration_prealloc)
        );
    }
    println!("=========================================================================================================================");
}