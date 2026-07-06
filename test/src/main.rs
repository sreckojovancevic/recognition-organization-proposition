mod entity;
mod recognition;
mod channel;
mod engine;
mod stress_test;
mod benchmark;
mod benchmark_engine;  // <-- NOVO

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() > 1 && args[1] == "bench" {
        println!("🚀 Pokrećem benchmark...\n");
        benchmark::main();
    } else if args.len() > 1 && args[1] == "bench2" {
        benchmark_engine::run_engine_benchmark();
    } else {
        println!("🧪 Pokrećem stres testove...\n");
        stress_test::run_all_tests();
        println!("\n💡 Komande:");
        println!("   cargo run --release -- bench   → Benchmark implementacija");
        println!("   cargo run --release -- bench2  → Benchmark Engine vs sort()");
        println!("   cargo run --release -- test    → Stres test (default)");
    }
}