// Needs Rust installed, or Docker. Run:  nishachar run examples/fizzbuzz.rs
fn main() {
    for n in 1..=15 {
        let out = match (n % 3, n % 5) {
            (0, 0) => "FizzBuzz".to_string(),
            (0, _) => "Fizz".to_string(),
            (_, 0) => "Buzz".to_string(),
            _ => n.to_string(),
        };
        println!("{out}");
    }
}
