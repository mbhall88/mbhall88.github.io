---
title: "Can dorado polish replace Clair3 for bacterial variant calling?"
description: Benchmarking dorado polish --vcf against Clair3 on the NanoVarBench data, and a simple filter that changes the answer for SNPs.
date: 2026-10-05T08:09:00+10:00
draft: true
has_table: true
tags:
  - variant-calling
  - dorado
  - clair3
  - nanopore
  - benchmarking
ShowToc: "true"
math: true
---

> **If you use these results, please cite the paper they build on:**
> Hall MB, *et al.* Benchmarking reveals superiority of deep learning variant callers on
> bacterial nanopore sequence data. *eLife* 13:RP98300 (2024)
> {{< cite "10.7554/eLife.98300" >}}.

## TL;DR

I reran our bacterial nanopore variant calling benchmark {{< cite "10.7554/eLife.98300" >}}
with the latest tools, and added ONT's `dorado polish --bacteria --vcf` alongside Clair3
{{< cite "10.1038/s43588-022-00387-x" >}}.

- **SNPs:** with the paper's Clair3 settings, Dorado is better at 5x and 10x depth, mostly
  because Clair3 misses more SNPs. From 25x they are tied.
- **Indels:** Clair3 is better at nearly every depth, by the most at low depth (hac 5x median F1
  0.896 vs 0.796).
- **Why Clair3 misses SNPs at low depth:** `--haploid_precise` throws away the variants Clair3
  calls as heterozygous. Running Clair3 diploid and keeping a het when its allele frequency is
  ≥0.65 gives Clair3 the best SNP *and* indel results of anything I tested.
- **Dorado's default filter is too lenient at low depth.** At 5x, its `PASS` calls include many
  low-quality false positives. Its QUAL score separates them well, though, so filtering on
  QUAL helps a lot.
- **Speed:** Dorado takes about 5 seconds per 50x bacterial genome on an H100 GPU. On CPU it
  takes about a minute, like Clair3, but needs about 10 GB of RAM.

## Background

In our [eLife paper][paper] {{< cite "10.7554/eLife.98300" >}} we benchmarked variant callers on
ONT reads from 14 bacterial species, using truth sets made by mutating each sample's own
reference genome. Clair3 came out on top. Since then, three things have changed:

1. ONT now presents [`dorado polish`][dorado] with `--vcf` as a way to call variants against a
   haploid reference. Its `--bacteria` model was trained for polishing bacterial assemblies.
2. Clair3 has moved to version 2 (PyTorch), and minimap2 {{< cite "10.1093/bioinformatics/bty191" >}}
   gained the `lr:hq` preset, which [did slightly better for variant calling][lrhq] in my
   earlier post.
3. Ryan Wick's [Dorado v2 polishing post][ryan-v2] suggested running `dorado polish` with
   `--vcf` and filtering the proposed changes, if bad changes can be told apart by quality score.
   That is a variant calling question, and our data can answer it.

So the question for this post is simple:

> *Is `dorado polish --bacteria --vcf` as good as Clair3 for bacterial variant calling, and
> what does it cost?*

## Methods

The [workflow][workflow] lives in the NanoVarBench repository, next to the paper's pipeline,
and every number in this post can be regenerated from it. Here is the outline.

**Data.** All 14 samples from the paper, using the hac and sup simplex reads basecalled with
Dorado v4.3.0 that we deposited in the SRA, and the truth sets [on Zenodo][truth]. Reads were
filtered to ≥1,000 bp and Q≥10.

**Depth.** Reads were subsampled to 5, 10, 25 and 50x with [`rasusa aln`][rasusa]
{{< cite "10.21105/joss.03941" >}}, which caps the depth at each position rather than
picking reads at random. This keeps high-copy plasmids from using up the read budget, and gives
much more even coverage than the paper's random subsampling. So low-depth recall here is **not**
directly comparable with the paper's figures. It is the same for every arm in this post,
though.

**Variant calling.** I compared four arms, each changing one thing from the one before:

| Arm | Aligner | Caller | Model |
| :--- | :--- | :--- | :--- |
| A (paper) | minimap2 2.26 `map-ont` | Clair3 1.0.5 | v4.3.0 hac/sup |
| B (`lr:hq` post) | minimap2 2.31 `lr:hq` | Clair3 1.0.5 | v4.3.0 hac/sup |
| C (current Clair3) | minimap2 2.31 `lr:hq` | Clair3 2.0.3 | v4.3.0 hac/sup, converted to PyTorch |
| D (Dorado) | minimap2 2.31 `lr:hq` | `dorado polish` 2.1.2 | `--bacteria` |

Clair3 ran with the paper's options (`--haploid_precise --include_all_ctgs --no_phasing_for_fa
--enable_long_indel`). Dorado ran with `--bacteria --vcf --min-depth 2`, matching Clair3's
minimum depth. C and D used the *same* alignment file, so the caller is the only difference
between them.

> **Getting public FASTQs into `dorado polish`.** Dorado expects a BAM from `dorado aligner`
> with an `@RG` header line naming the basecalling model, and refuses anything else ("Input BAM
> file was not aligned using Dorado."). Reads downloaded from the SRA have neither. Two changes
> make a minimap2 BAM work: add a single `@RG` line with
> `DS:basecall_model=dna_r10.4.1_e8.2_400bps_hac@v4.3.0` (with `samtools reheader`), and pass
> the hidden `--any-bam` flag. Per-read `RG` tags aren't needed. I checked this against
> `dorado aligner` on one sample: the calls were identical, though the QUAL values of some
> records differed slightly.

**Evaluation.** Every arm's calls went through the same filtering as the paper, and were
scored with vcfdist {{< cite "10.1038/s41467-023-43876-x" >}} v2.6.4. I report two scores:

- **Best F1:** the best F1 over all QUAL thresholds, i.e. what you get if you tune a
  threshold.
- **Default-PASS:** only the calls the caller marks `PASS`, i.e. what you get out of the box.

All numbers are medians over the 14 samples unless stated otherwise.

## Results

### SNPs: Dorado is better at low depth

{{< figure src="best-f1-depth.png" alt="Median F1 against depth for SNPs and indels, hac and sup reads, for each arm." caption="**Figure 1:** Median F1 over the 14 samples against depth, for SNPs (top) and indels (bottom) with hac (left) and sup (right) reads. Solid lines are Best F1; dashed lines with open markers are the Default-PASS score, for Arms C and D and the AF filter. F1 is on a logit scale, which spreads out the differences close to 1. Depth is a per-position cap, not a random genome-wide subsample, so low-depth results aren't directly comparable with the paper's. Arm C + AF filter (0.65) is Clair3 run diploid, with each heterozygous call made the alternative allele when its allele frequency is at least 0.65 and the reference otherwise (see below); it is an extra analysis, not one of the four arms." >}}

At 5x and 10x, Dorado calls SNPs better than Clair3 (Figure 1, top row):

| Reads | Depth | Clair3 (C) | Dorado (D) |
| :--- | ---: | ---: | ---: |
| hac | 5x | 0.9900 | 0.9910 |
| hac | 10x | 0.9957 | 0.9990 |
| sup | 5x | 0.9945 | 0.9972 |
| sup | 10x | 0.9981 | 0.9997 |

The difference is almost all missed SNPs. Summed over the samples at hac 10x, Clair3 misses
2,478 SNPs and Dorado 320, while Dorado has a few more false positives (190 vs 72). From 25x the
two are tied to four decimal places. At 50x Clair3 is marginally ahead, because Dorado makes
more false positives (19 vs 1 for hac).

### Indels: Clair3 is better

Indels are the other way around. Clair3 is ahead at almost every depth, and by the most at low
depth: at hac 5x its median F1 is 0.896 against Dorado's 0.796. Even at 50x Clair3 leads (hac
0.990 vs 0.978; sup 0.995 vs 0.990). sup at 10x is the one place Dorado is ahead, and only
just (0.975 vs 0.972).

### Why Clair3 misses SNPs, and a simple fix

Clair3's models are diploid. `--haploid_precise` keeps only the calls Clair3 makes as
homozygous, and throws away anything it calls heterozygous. In bacteria, a "heterozygous" call
often happens in repeats, where reads from another copy of the repeat pile up at the same
position and make the true variant look like it is only on some of the reads. On one *E. coli*
sample at hac 50x, 46 of Clair3's 50 missed SNPs were dropped this way.

Clair3's `--haploid_sensitive` mode keeps those calls, but it also keeps minority alleles at
around 20% frequency, which QUAL can't separate from the real ones. Allele frequency can. So I
ran Clair3 without either haploid flag (diploid), and turned each heterozygous call into the
alternative allele if its allele frequency (`FORMAT/AF`) was at least 0.65, or the reference
otherwise. Homozygous calls were left alone. [The script][af-script] is short.

| Reads | Depth | Clair3 | Clair3 + AF filter | Dorado |
| :--- | ---: | ---: | ---: | ---: |
| hac | 5x | 0.9900 | **0.9949** | 0.9910 |
| hac | 10x | 0.9957 | **0.9992** | 0.9990 |
| sup | 5x | 0.9945 | **0.9977** | 0.9972 |
| sup | 10x | 0.9981 | **0.9998** | 0.9997 |

*SNP Best F1.*

With the filter, Clair3 matches or beats Dorado on SNPs at every depth. At hac 10x its missed
SNPs fall from 2,478 to 304, at the cost of 78 more false positives. Its indels get no worse,
and improve a little at low depth (sup 5x: 0.935 to 0.950).

One threshold works across samples, depths and read models. I tested 0.50 to 0.80 in steps of
0.05, and 0.65 was best overall. Compared with each sample's own best threshold, the typical
sample loses nothing at 0.65, and the worst loses 0.001 SNP F1 and 0.017 indel F1. 0.70 and 0.75
are almost as good. Below 0.65 things go wrong at 5x, where 3 of 5 reads is an allele frequency
of 0.6 and too many false positives get through. I picked 0.65 from the same data I'm reporting,
so treat these numbers as slightly optimistic.

### Dorado's default filter is too lenient at low depth

The dashed lines in Figure 1 show what you get without tuning a threshold. Clair3's `PASS`
filter costs it very little. Dorado's costs a lot at low depth: at hac 5x its indel F1 falls
from 0.796 (Best F1) to 0.419 (Default-PASS).

The problem isn't that Dorado filters too much, but too little. At hac 5x, Dorado's `PASS`
calls include 9,540 false positive indels across the samples, against 503 at the best
threshold. Dorado marks fewer than 4% of its records `LowQual`.

{{< figure src="pr-curves.png" alt="Precision-recall curves over QUAL for each arm at 10x and 50x." caption="**Figure 2:** Precision-recall curves over QUAL thresholds at 10x and 50x, for SNPs (top) and indels (bottom). Each curve pools all 14 samples, summing their true and false calls at each threshold. Markers show each arm's Default-PASS score, pooled the same way. Each panel is zoomed to its own range. Arm C + AF filter (0.65) is Clair3 run diploid, with each heterozygous call made the alternative allele when its allele frequency is at least 0.65 and the reference otherwise (see above); it is an extra analysis, not one of the four arms." >}}

That answers Ryan's question: Dorado's QUAL *does* separate bad calls from good ones, at least
at low depth (Figure 2). The best threshold depends on depth, though. Here is Dorado's indel F1
at a few fixed thresholds:

| Reads | Depth | Best F1 | Default-PASS | QUAL ≥ 5 | QUAL ≥ 10 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| hac | 5x | 0.796 | 0.419 | 0.565 | 0.755 |
| hac | 10x | 0.927 | 0.872 | 0.910 | 0.923 |
| hac | 50x | 0.978 | 0.973 | 0.974 | 0.966 |
| sup | 5x | 0.910 | 0.783 | 0.854 | 0.905 |
| sup | 50x | 0.990 | 0.987 | 0.988 | 0.982 |

QUAL ≥ 10 fixes most of the low-depth problem but costs a little at 50x. For SNPs the default
costs much less (hac 5x: 0.986 vs 0.991).

### Per sample

{{< figure src="per-sample-best-f1.png" alt="Best F1 per sample at each depth for each arm, with dnd samples shaded." caption="**Figure 3:** Best F1 for every sample at every depth, for SNPs and indels with hac and sup reads. F1 is on a logit scale and each panel has its own axis. A perfect score (F1 = 1) has no place on a logit scale, so perfect scores are drawn in their own column after the dotted line. The two shaded samples, *S. enterica* and *V. parahaemolyticus*, carry *dnd* phosphorothioate systems ([dorado#1599](https://github.com/nanoporetech/dorado/issues/1599)). Arm C + AF filter (0.65) is Clair3 run diploid, with each heterozygous call made the alternative allele when its allele frequency is at least 0.65 and the reference otherwise (see above); it is an extra analysis, not one of the four arms." >}}

The pattern holds across samples (Figure 3). At hac 10x, Dorado beats the paper's Clair3
settings on SNPs for 13 of the 14 samples, and Clair3 beats Dorado on indels for all 14 at hac
5x. Dorado's weakest indel results are *K. pneumoniae* and *M. tuberculosis* at low depth.

There is a [known issue][dnd] where Dorado's bacterial model makes systematic errors in genomes
with *dnd* phosphorothioate modifications, such as *Salmonella enterica*. Our *S. enterica* and
*V. parahaemolyticus* samples have *dnd* systems, but they don't stand out here. That issue was
reported for reads basecalled with hac v6.0, and our reads are v4.3.0.

### Newer Clair3 and `lr:hq` change little

Arms A, B and C are almost indistinguishable in Figure 1. Moving from `map-ont` to `lr:hq`
changed median Best F1 by at most 0.0003. Moving from Clair3 1.0.5 to 2.0.3 with the same (converted)
models gave identical Best F1 for every sample, depth and read model. Clair3 2.0.3 is faster,
though.

### Runtime and memory

Median per 50x read set, over 28 read sets (14 samples, hac and sup), on 8 threads of an AMD EPYC
9745 or one NVIDIA H100:

| Step | Tool | Device | Wall time | Peak RAM |
| :--- | :--- | :--- | ---: | ---: |
| Alignment | minimap2 2.31 `lr:hq` | CPU | 12 s | 0.9 GB |
| Variant calling | Clair3 1.0.5 | CPU | 61 s | 1.2 GB |
| Variant calling | Clair3 2.0.3 | CPU | 49 s | 1.0 GB |
| Variant calling | `dorado polish` | GPU | 4.6 s | 1.4 GB |
| Variant calling | `dorado polish` | CPU | 59 s | 9.7 GB |

{{< figure src="runtime-memory.png" alt="Wall time and peak RAM of variant calling against depth for each arm, on log scales." caption="**Figure 4:** Wall time (left) and peak RAM (right) of variant calling against depth, both on log scales. Points are medians over the 28 read sets (14 samples, hac and sup) and bars show the range. Clair3 (Arms A-C) ran on 8 threads of an AMD EPYC 9745, and `dorado polish` (Arm D) on one NVIDIA H100 with 8 threads. The open marker is Dorado run on 8 CPU threads at 50x, for timing only. Alignment isn't shown. Peak RAM is host memory: Dorado's GPU memory isn't measured." >}}

On a GPU, Dorado is at least ten times faster than Clair3 at every depth (Figure 4). On CPU it
takes about as long, but needs much more memory. One oddity: Clair3 took *longer* at 5x and
10x (two to three minutes) than at 50x, and used more memory too. I haven't looked into why.
The full breakdown, including alignment, is in [Table 1](table1-runtime-memory.csv).

## Why not Clair3's bacterial model?

Clair3 now ships a model fine-tuned on bacteria (`r1041_e82_400bps_sup_v430_bacteria_finetuned`),
which would be the obvious "latest" choice. I deliberately left it out: it was trained on 12 of
these 14 samples, so testing it here would mean scoring it on its own training data.

## Caveats

- **Only v4.3.0 reads.** These are the reads from the paper. Newer basecalling models give
  more accurate reads, and both callers may do better on them.
- **`dorado smallvar` wasn't tested properly.** Dorado's new small variant caller only has
  models for hac v5.2.0 and v6.0.0 reads. I tried forcing the v6.0.0 model onto our v4.3.0 reads
  on three samples. It was worse than both other callers on SNPs, but competitive on indels.
  A fair test needs rebasecalled reads.
- **Newer polishing models and duplex reads** weren't tested, for the same reason.
- **The AF filter threshold** was chosen on the same data.
- **Depth capping** gives more even coverage than you would see in practice, so real low-depth
  data may do worse than shown here, for every caller.

## Conclusion

If you are calling variants in bacterial genomes from ONT reads:

- **Clair3 is still the best overall**, especially for indels. If you use `--haploid_precise`,
  consider running Clair3 diploid with an allele frequency filter instead: it recovers the
  SNPs that `--haploid_precise` throws away, at no cost to indels.
- **`dorado polish --vcf` is a reasonable choice for SNPs**, particularly if you have a GPU
  and want speed. Don't trust its `PASS` filter at low depth: filter on QUAL (around 10 at
  5–10x). Its indels lag behind Clair3's.

## Acknowledgements

Thanks to Ryan Wick, whose polishing posts prompted this, and for reviewing a draft.

## Appendix

The [workflow][workflow], the aggregated tables and the figures are in the NanoVarBench
repository.

{{< csv-table src="table-s1-per-sample.csv" caption="Table S1: Per-sample results for every arm, depth and read model, with actual depths" >}}

{{< share-file src="table-s1-per-sample.csv" >}}

{{< share-file src="table1-runtime-memory.csv" >}}

[paper]: https://doi.org/10.7554/eLife.98300
[dorado]: https://github.com/nanoporetech/dorado
[lrhq]: {{< ref "post/minimap2-lrhq-preset-testing" >}}
[ryan-v2]: https://rrwick.github.io/2026/06/19/dorado-v2-polishing.html
[workflow]: https://github.com/mbhall88/NanoVarBench/tree/main/updates/2026-dorado-polish
[truth]: https://zenodo.org/records/10867171
[rasusa]: https://github.com/mbhall88/rasusa
[af-script]: https://github.com/mbhall88/NanoVarBench/blob/main/updates/2026-dorado-polish/workflow/scripts/af_filter.py
[dnd]: https://github.com/nanoporetech/dorado/issues/1599
