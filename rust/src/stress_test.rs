// ==========================================================
// STRESS / PROPERTY TESTS
// ==========================================================

use rand::Rng;
use std::time::Instant;

use crate::engine::RecognitionTopologyEngine;

pub fn run_all_tests() {
    let mut engine = RecognitionTopologyEngine::new();

    readme_test(&mut engine);
    tricky_test(&mut engine);
    stress_test(&mut engine);
}

// ----------------------------------------------------------

fn readme_test(engine: &mut RecognitionTopologyEngine) {

    let words = vec![
        "apple",
        "banana",
        "apricot",
        "cherry",
        "level",
        "radar",
    ];

    let got = engine.organize(&words);

    let mut expected =
        words.iter().map(|s| s.to_string()).collect::<Vec<_>>();

    expected.sort();

    assert_eq!(got, expected);

    println!("✔ README test passed.");
}

// ----------------------------------------------------------

fn tricky_test(engine: &mut RecognitionTopologyEngine) {

    let words = vec![
        "ab",
        "azb",
        "az",
        "ab",
        "",
        "a",
        "aab",
        "b",
    ];

    let got = engine.organize(&words);

    let mut expected =
        words.iter().map(|s| s.to_string()).collect::<Vec<_>>();

    expected.sort();

    assert_eq!(got, expected);

    println!("✔ Tricky cases passed.");
}

// ----------------------------------------------------------

fn stress_test(engine: &mut RecognitionTopologyEngine) {

    const TESTS: usize = 100_000;

    let mut rng = rand::thread_rng();

    let chars: Vec<char> =
        ('a'..='z').collect();

    let start = Instant::now();

    for i in 0..TESTS {

        let num_words =
            rng.gen_range(0..=200);

        let mut words: Vec<String> =
            Vec::new();

        for _ in 0..num_words {

            // 30% duplicate
            if !words.is_empty()
                && rng.gen_bool(0.30)
            {
                let idx =
                    rng.gen_range(0..words.len());

                words.push(words[idx].clone());

                continue;
            }

            // 5% empty string
            if rng.gen_bool(0.05) {
                words.push(String::new());
                continue;
            }

            let len =
                rng.gen_range(0..=64);

            let word: String =
                (0..len)
                    .map(|_| {
                        chars[
                            rng.gen_range(
                                0..chars.len()
                            )
                        ]
                    })
                    .collect();

            words.push(word);
        }

        let refs: Vec<&str> =
            words.iter()
                .map(|s| s.as_str())
                .collect();

        let got =
            engine.organize(&refs);

        let mut expected =
            words.clone();

        expected.sort();

        assert_eq!(
            got,
            expected,
            "Failure on iteration {}",
            i
        );

        if (i + 1) % 100_000 == 0 {

            println!(
                "✔ {} / {} tests ({:?})",
                i + 1,
                TESTS,
                start.elapsed()
            );
        }
    }

    println!();
    println!("==================================");
    println!("All {} stress tests passed.", TESTS);
    println!("Elapsed: {:?}", start.elapsed());
    println!("==================================");
}