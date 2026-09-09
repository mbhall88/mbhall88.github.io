# Measured minimizer counts for panel 1

The diagram is modelled on **SRR26465526**, an Oxford Nanopore read set where
normalisation rescued a severe genome-size underestimate. The diagram is an
illustrative redraw, not a replacement for the measured histogram saved here.

## What was measured

The counts come directly from LRGE v1.0.0's depth-skew detector, before
normalisation. They are count-min-sketch estimates for its bottom-k sample of
65,536 distinct minimizers, not reference-mapping depths or a histogram of all
minimizer occurrences. Detection used seed 4556 and sampled 1,338 of 132,633 reads.
The input contains 743,666,544 bases.

The median count is 1 and the 99.9th percentile is 426, giving a skew score of
426, well above the threshold of 16. Only 496 of the 65,536 distinct minimizers
have counts of at least 16. The high-count population is consequently much
smaller than the low-count population, even though each of those minimizers
occurs many times. The binned plot shows local peaks around 250–290 and 400–465.
The counts alone do not identify the sequence responsible for the excess.

Both plot axes are logarithmic. Bars show numbers of distinct minimizers per
bin; integer-aligned bins are approximately equally wide in log count above
the lowest counts. The plot is not a density per unit of linear count and is
not smoothed. Amber highlights the high-count region, not a biological annotation.

The detector median of 1 is **not** the full-input baseline `m` used for retention.
For this input, the recorded full-input baseline is 31. Panel 3 deliberately
keeps its separate illustrative example of `m = 20`.

## Why this sample

The saved benchmark results (`SRR26465526-benchmark.tsv`) report:

| Setting | Genome-size estimate |
|---|---:|
| Without normalisation (`never`) | 27,170 bp |
| With normalisation (`norm`) | 2,214,342 bp |
| Benchmark truth | 2,230,369 bp |

Thus normalisation changes the estimate from 1.22% to 99.28% of the benchmark
truth. Internal-match filtering is off in both arms. These are recorded
benchmark estimates, not a new overlap benchmark run for this figure.
The freshly extracted detector score (426) and sampled-read count (1,338)
match that benchmark's log. Input record and base counts match too.

SRR10353548 was also checked; its histogram has a smaller high-count bump around
250–400, a median of 1 and a 99.9th percentile of 281. Its counts and a comparison
plot are included as supporting data, but panel 1 uses SRR26465526.

## Reproduction

`extract/` contains a small diagnostic binary using copies of LRGE's
`depth_skew.rs` and `io.rs` from commit
`01669fe358e3c6aec7328d5e4c238bdeb0eb2397`. These two source files are unchanged
between that commit and tag `lrge-1.0.0`. The only modification to the detector
prints the count-frequency table in `depth_skew_report`, immediately after
sorting the counts. No sampling, minimizer extraction, sketch or quantile logic
was changed. `Cargo.lock` preserves the upstream dependency versions used here.

```bash
cargo build --release --locked --manifest-path normalisation-example/extract/Cargo.toml
normalisation-example/extract/target/release/lrge-detector-histogram \
  /scratch/user/uqmhal11/lrge-issue29/SRR26465526/SRR26465526.fastq.gz 4556 \
  > normalisation-example/SRR26465526.tsv \
  2> normalisation-example/SRR26465526.log
python normalisation-example/plot_counts.py
```

The plotting script requires NumPy and matplotlib. The read path is specific
to this workspace; use the same retained input to reproduce the exact counts.
The FASTQ itself is not included. The raw two-column TSVs are sufficient to
reproduce the plots without downloading reads or running the detector.

The benchmark source is LRGE's
[`issue36_filter_benchmark_summary.tsv`](https://github.com/mbhall88/lrge/blob/lrge-1.0.0/paper/corrections/issue36_filter_benchmark_summary.tsv);
the local detailed results were retained from
`/scratch/user/uqmhal11/lrge-filter/runs/SRR26465526/summary.tsv`.
