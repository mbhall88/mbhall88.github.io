#![allow(dead_code)]
mod io;
mod depth_skew;
pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let seed = args.get(2).map(|s| s.parse::<u64>().unwrap()).unwrap_or(42);
    let mut detector = depth_skew::DepthSkewDetector::new(Some(seed));
    let n = io::count_records(&args[1], |sequence| {
        detector.observe(sequence);
        Ok(())
    })?;
    let detection = detector.finish();
    eprintln!("input={} seed={} records={} {}", args[1], seed, n, detection.report);
    Ok(())
}
