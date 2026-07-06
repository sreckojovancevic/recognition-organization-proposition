use std::time::Instant;
use rand::Rng;

// =========================================================================
// UVOZ TVOJIH MODULA
// =========================================================================
use crate::engine::RecognitionTopologyEngine;

// =========================================================================
// GENERISANJE TESTOVA
// =========================================================================
fn generate_strings(size: usize, max_len: usize) -> Vec<String> {
    let mut rng = rand::thread_rng();
    let chars: Vec<char> = ('a'..='z').collect();
    
    (0..size)
        .map(|_| {
            let len = rng.gen_range(1..=max_len);
            (0..len)
                .map(|_| chars[rng.gen_range(0..chars.len())])
                .collect()
        })
        .collect()
}

// =========================================================================
// FORMATIRANJE
// =========================================================================
fn format_duration(d: std::time::Duration) -> String {
    if d.as_secs() > 0 {
        format!("{:.2} s", d.as_secs_f64())
    } else if d.as_millis() > 0 {
        format!("{:.2} ms", d.as_nanos() as f64 / 1_000_000.0)
    } else {
        format!("{:.2} µs", d.as_nanos() as f64 / 1_000.0)
    }
}

// =========================================================================
// BENCHMARK 2: ENGINE vs STANDARD SORT
// =========================================================================
pub fn run_engine_benchmark() {
    let sizes = vec![100, 1_000, 10_000, 100_000];
    let iterations = 3;
    let max_len = 10;

    println!("\n");
    println!("=================================================================================");
    println!(" 📊 BENCHMARK 2: Recognition Engine vs Standard Sort");
    println!("    (na stvarnim stringovima, bez veštačkih bucket-ova)");
    println!("=================================================================================");
    println!(" {:<10} | {:<20} | {:<20} | {:<12} | {:<12}", 
        "Size", "Engine (avg)", "sort() (avg)", "Ratio", "Faster");
    println!("---------------------------------------------------------------------------------");

    let mut engine = RecognitionTopologyEngine::new();

    for &size in &sizes {
        let mut engine_times = Vec::with_capacity(iterations);
        let mut sort_times = Vec::with_capacity(iterations);
        let mut last_engine_result = Vec::new();
        let mut last_sort_result = Vec::new();

        for i in 0..iterations {
            let data = generate_strings(size, max_len);

            // Engine
            let start = Instant::now();
            let engine_result = engine.organize(&data.iter().map(|s| s.as_str()).collect::<Vec<_>>());
            let engine_dur = start.elapsed();
            engine_times.push(engine_dur);
            if i == 0 { last_engine_result = engine_result; }

            // Standard sort
            let mut sort_data = data.clone();
            let start = Instant::now();
            sort_data.sort();
            let sort_dur = start.elapsed();
            sort_times.push(sort_dur);
            if i == 0 { last_sort_result = sort_data; }

            // Provera ispravnosti
            if i == 0 {
                assert_eq!(last_engine_result, last_sort_result, 
                    "❌ Engine i sort() daju različite rezultate za size={}", size);
            }
        }

        let avg_engine = engine_times.iter().sum::<std::time::Duration>() / iterations as u32;
        let avg_sort = sort_times.iter().sum::<std::time::Duration>() / iterations as u32;

        let ratio = if avg_engine < avg_sort {
            avg_sort.as_secs_f64() / avg_engine.as_secs_f64()
        } else {
            avg_engine.as_secs_f64() / avg_sort.as_secs_f64()
        };

        let faster = if avg_engine < avg_sort { "Engine 🚀" } else { "sort() 🦀" };

        println!(" {:<10} | {:<20} | {:<20} | {:<12.2}x | {:<12}", 
            size,
            format_duration(avg_engine),
            format_duration(avg_sort),
            ratio,
            faster
        );
    }

    println!("=================================================================================");
    println!("✅ Benchmark 2 završen.");
    println!("\n💡 Ovo meri stvarnu cenu Recognition Engine-a u odnosu na standardni sort.");
}