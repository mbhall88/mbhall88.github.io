---
ShowToc: 'true'
date: 2026-10-06 16:08:00+10:00
description: Benchmarking `dorado polish` against Clair3, plus an allele frequency
  filter that improves on Clair3, the existing gold standard.
doi: 10.5281/zenodo.23184310
draft: false
has_table: true
images:
- social-preview.png
math: true
tags:
- variant-calling
- dorado
- clair3
- nanopore
- benchmarking
title: Comparing Dorado polish to Clair3 for bacterial variant calling
---


> **If you use these results, please cite the paper they build on:**
> Hall MB, *et al.* [Benchmarking reveals superiority of deep learning variant callers on
> bacterial nanopore sequence data][paper]. *eLife* 13:RP98300 (2024).
> doi:[10.7554/eLife.98300][paper]

## TL;DR

I reran our bacterial nanopore variant calling benchmark {{< cite "10.7554/eLife.98300" >}}
with a couple of updated tools. I then compared the paper's best caller, Clair3
{{< cite "10.1038/s43588-022-00387-x" >}} with ONT's
[`dorado polish`][dorado-docs].

- **SNPs:** Clair3, run in (default) diploid mode, with an allele frequency (AF) filter in place of
  `--haploid_precise`, had the highest median SNP F1 score at every depth with both read models. With sup reads its lead over Dorado
  grows from 25x up: at 50x it made 23 SNP errors over the 14 genomes, against Dorado's 83.
- **Clair3 with the paper's settings vs Dorado:** Dorado calls SNPs better at 5x and 10x, predominantly via improved recall. The two are level at 25x, and Clair3 is slightly ahead at 50x.
- **Indels:** Clair3 is better at nearly every depth. At 50x its median F1 is 0.990 against
  Dorado's 0.978 for hac, and 0.995 against 0.990 for sup.
- **Default filters:** Dorado's `PASS` filter lets too much through at low depth. Its QUAL
  scores sort good calls from bad well, so filtering on QUAL fixes most of this.
- **Speed:** Dorado takes about 5 seconds for a 50x bacterial genome on an H100 GPU. On CPU it
  takes about a minute, as Clair3 does, but needs about 10 GB of RAM.

> In practice, at 50x either tool will give you nearly the same SNPs, with fewer than ten errors
> per genome. If you want the best you can get, down to single SNPs, use Clair3 with the AF
> filter.

## Background

In our [eLife paper][paper] {{< cite "10.7554/eLife.98300" >}} we benchmarked variant callers on
ONT reads from 14 bacterial species, using truth sets made by mutating each sample's own
reference genome. We found Clair3 came out on top, but three things have changed since:

1. ONT now offers [`dorado polish`][dorado-docs] with `--vcf` as a way to call variants
   against a haploid reference. Its `--bacteria` model was trained for polishing bacterial
   assemblies.
2. Clair3 is now at version 2 (PyTorch), and minimap2 {{< cite "10.1093/bioinformatics/bty191" >}}
   has a new `lr:hq` preset, which [did slightly better for variant calling][lrhq] in my
   earlier post.
3. In his [Dorado v2 polishing post][ryan-v2], Ryan Wick suggested a more controlled way to
   polish: run `dorado polish` with `--vcf`, filter the proposed changes, and apply only the
   high-confidence ones. That works only if the bad changes can be told apart, by quality
   score, depth or something else. Ryan and I then talked about me rerunning the paper's
   benchmark to see how Dorado does as a variant caller, and this post is the result. Thanks
   to Ryan for getting it started.

So the question for this post is:

> *How does `dorado polish --bacteria --vcf` compare with Clair3 for bacterial variant
> calling, and what does it cost to run?*

## Methods

The [workflow][workflow] lives in the paper's [NanoVarBench](https://github.com/mbhall88/NanoVarBench/) repository.
The variant calls and vcfdist outputs are on [Zenodo][zenodo].

### Data
All 14 samples (species) from the paper. I used the hac and sup simplex reads, basecalled with
Dorado v4.3.0, that we deposited in the SRA[^reads], and the truth sets [on Zenodo][truth].
Reads were filtered to ≥1,000 bp and Q≥10.

### Depth
Reads were subsampled to 5, 10, 25 and 50x with [`rasusa aln`][rasusa]
{{< cite "10.21105/joss.03941" >}}. It caps the depth at each position by taking a random
selection of the reads there, which stops high-copy plasmids from using up the read budget
and gives more even coverage than the paper's genome-wide subsampling[^depth].

### Variant calling 
I compared four arms:

| Arm | Aligner | Caller | Model |
| :--- | :--- | :--- | :--- |
| A (paper) | minimap2 2.26 `map-ont` | Clair3 1.0.5 | v4.3.0 hac/sup |
| B (`lr:hq` post) | minimap2 2.31 `lr:hq` | Clair3 1.0.5 | v4.3.0 hac/sup |
| C (current Clair3) | minimap2 2.31 `lr:hq` | Clair3 2.0.3 | v4.3.0 hac/sup, converted to PyTorch |
| D (Dorado) | minimap2 2.31 `lr:hq` | `dorado polish` 2.1.2 | `--bacteria` |

Clair3 ran with the paper's options (`--haploid_precise --include_all_ctgs --no_phasing_for_fa
--enable_long_indel`). Dorado ran with `--bacteria --vcf --min-depth 2`, which matches Clair3's
minimum depth. C and D used the *same* alignment file, so the caller is the only difference
between them[^any-bam].

### Clair3 with an AF filter 
Clair3's models are diploid. A bacterial chromosome is haploid, so a heterozygous ("het") call has to become one allele or
the other, and Clair3's two haploid modes do this in opposite ways. `--haploid_precise`
keeps only the homozygous calls and drops every het. `--haploid_sensitive` keeps every het as
a variant. As a fifth line in the figures, I ran Clair3 (Arm C) with neither flag, and turned
each het into the ALT if the ALT's allele frequency (`FORMAT/AF`, the fraction of reads carrying
it) was ≥ 0.65, and into the reference otherwise. See [this
script][af-script]. Here is what each mode does with a SNP:

| Clair3's diploid call | `--haploid_precise` | `--haploid_sensitive` | AF filter (≥ 0.65) |
| :--- | :---: | :---: | :---: |
| 1/1 | ALT | ALT | ALT |
| 0/1, ALT AF 0.90 | REF | ALT | ALT |
| 0/1, ALT AF 0.65 | REF | ALT | ALT |
| 0/1, ALT AF 0.40 (REF 0.60) | REF | ALT | REF |
| 0/1, ALT AF 0.20 | REF | ALT | REF |

At a site with two ALTs (1/2), the filter takes the ALT with the higher AF if it is ≥ 0.65,
and the reference otherwise. I chose 0.65 by testing thresholds from 0.50 to 0.80 in steps of
0.05 ([see here][af-sweep]), on the same data. 0.65 was best overall. Below it, too many false
positives get through at 5x, where 3 of 5 reads is an AF of 0.6. Since the threshold was
picked on the data I report, treat the AF filter's numbers as slightly optimistic.

### Evaluation
Every call set went through the same filtering as the paper, and was scored
with vcfdist {{< cite "10.1038/s41467-023-43876-x" >}} v2.6.4. QUAL is the caller's
Phred-scaled confidence in each call (the VCF `QUAL` column). I report two scores:

- **Best F1:** the best F1 over all QUAL thresholds, i.e. what you get if you tune a
  threshold.
- **Default-PASS:** only the calls the caller marks `PASS`, i.e. what you get out of the box.

All numbers are medians over the 14 samples unless stated otherwise. Where I give error counts,
they are false negatives plus false positives, summed over the samples.

## Results

### SNPs: Clair3 with the AF filter is best

{{< figure src="best-f1-depth.png" alt="Median F1 against depth for SNPs and indels, hac and sup reads, for each arm and for Clair3 with the AF filter." caption="**Figure 1:** Median F1 over the 14 samples against depth, for SNPs (top) and indels (bottom) with hac (left) and sup (right) reads. Solid lines are Best F1; dashed lines with open markers are the Default-PASS score, for Arms C and D and the AF filter. F1 is on a logit scale, which spreads out the differences close to 1. Points are 'jittered' (horizontally) so they don't hide each other; each belongs to the depth below it. AF is allele frequency, the fraction of reads carrying an allele. Arm C + AF filter (0.65) is Clair3 run diploid, with each heterozygous call made the alternative allele when its AF is ≥ 0.65 and the reference otherwise." >}}

Clair3 with the AF filter has the highest median SNP F1 at every depth, for both read models
(Figure 1, top row):

| Reads | Depth | Clair3 (C) | Clair3 + AF filter | Dorado (D) |
| :--- | ---: | ---: | ---: | ---: |
| hac | 5x | 0.99003 | **0.99489** | 0.99098 |
| hac | 10x | 0.99569 | **0.99918** | 0.99897 |
| hac | 25x | 0.99959 | **0.99981** | 0.99965 |
| hac | 50x | 0.99988 | **0.99990** | 0.99971 |
| sup | 5x | 0.99451 | **0.99771** | 0.99722 |
| sup | 10x | 0.99810 | **0.99979** | 0.99972 |
| sup | 25x | 0.99980 | **0.99994** | 0.99981 |
| sup | 50x | 0.99992 | **0.99998** | 0.99984 |

*Median SNP Best F1.*

These numbers are all close to 1, so error counts show the differences more clearly. At sup 50x,
Clair3 with the AF filter made 23 SNP errors over the 14 genomes, Clair3 with the paper's
settings 48, and Dorado 83. That is fewer than two errors per genome against about six.
Clair3 with the filter got a perfect SNP score on 6 of the 14 samples; Dorado did on 2.
At sup 25x the counts are 35, 218 and 89. With hac reads at 50x the gap is smaller (48, 98 and
122). Dorado's extra errors at 50x are mostly missed SNPs (71 vs 20 for sup, 103 vs 47 for
hac), plus a few more false positives (12 vs 3, and 19 vs 1).

Against Clair3 with the paper's settings, Dorado is better at 5x and 10x. The two are level
at 25x, and Clair3 is slightly ahead at 50x. At low depth the difference is mostly SNPs that
Clair3 misses. For example, at hac 10x Clair3 misses 2,478 of the 203,164 truth SNPs (1.2%) and
Dorado misses 320. Two-thirds of Clair3's misses come from three of the samples, though
Clair3 misses more than Dorado on 13 of the 14[^gap]. By 50x the gap is gone: Clair3 misses
97 and Dorado 103.

### Why Clair3 misses SNPs

The missing SNPs are mostly het calls that `--haploid_precise` throws away. In bacteria, a het
call often points to a mixed sample, or to variants that arose while the isolate was cultured.
Though repeats can also cause them. Reads from another copy of the repeat pile up at
the same position, so the variant looks as if it is on only some of the reads (Figure 2). On one
*E. coli* sample at hac 50x, 46 of Clair3's 50 missed SNPs were dropped this way. At low depth
many more true SNPs are called het: at hac 10x, the het calls the AF filter rescues have a
median AF of 0.8 to 0.9 in each sample.

{{< figure src="het-call-repeat.png" alt="Diagram: reads from a second repeat copy align to the first, making a true SNP look heterozygous, which --haploid_precise drops and the AF filter keeps." caption="**Figure 2:** How a repeat turns a true SNP into a het call. **a**, The sequenced genome has two similar copies of a repeat, like the two 7.5 kb copies, 96.5% identical, in our *E. coli* sample. The SNP (T) is in copy 1 only. **b**, Some reads from copy 2 align to copy 1 with full mapping quality (MAPQ 60), carrying the reference base (C), so only some of the reads at the SNP carry the ALT. The read counts are illustrative: at the SNPs Clair3 missed in this sample, 60–85% of reads carried the ALT. **c**, Clair3's diploid model calls the site heterozygous. `--haploid_precise` drops the call, and `--haploid_sensitive` and the AF filter both call the ALT. A mixed sample, with reads from another strain in place of the reads from copy 2, gives the same kind of pileup." >}}

`--haploid_sensitive` keeps those calls, but it also keeps minority alleles at around 20% AF,
and QUAL can't tell those apart from the real variants. With the filter, Clair3's
misses at hac 10x fall from 2,478 to 304, for 78 more false positives. Its indels are no worse
at any depth, and a little better at low depth (sup 5x: 0.935 to 0.950).

The 0.65 threshold works across samples, depths and read models. Compared with each
sample's own best threshold, the typical sample loses nothing at 0.65. The worst one loses
0.001 SNP F1 and 0.017 indel F1. **0.70 and 0.75 are almost as good.**

### Indels: Clair3 is better

Clair3 is ahead on indels at almost every depth: at 50x, 0.990 against 0.978 for hac and 0.995
against 0.990 for sup. The gap is largest at low depth (hac 5x: 0.896 vs 0.796). The one
place Dorado is ahead is sup at 10x, and only just (0.975 vs 0.972). The AF filter makes
almost no difference to Clair3's indels at 25x and 50x.

### Dorado's default filter is too lenient at low depth

The dashed lines in Figure 1 show what you get without tuning a threshold. Clair3's `PASS`
filter costs it very little. At 50x Dorado's costs little too (sup SNP F1 0.9998 either way),
but at low depth it costs a lot: at hac 5x its indel F1 falls from 0.796 (Best F1) to 0.419
(Default-PASS).

Dorado's filter lets too much through. At hac 5x its `PASS` calls include 9,540 false
positive indels across the samples, against 503 at the best threshold. Dorado marks fewer than
4% of its records `LowQual`.

{{< figure src="pr-curves.png" alt="Precision-recall curves over QUAL for each arm at 10x and 50x." caption="**Figure 3:** Precision-recall curves over QUAL thresholds at 10x and 50x, for SNPs (top) and indels (bottom). Each curve pools all 14 samples, summing their true and false calls at each threshold. Markers show each arm's Default-PASS score, pooled the same way. Each panel is zoomed to its own range. Arm C + AF filter (0.65) is as in Figure 1." >}}

So for Ryan's suggestion, Dorado's QUAL *does* separate bad calls from good ones, at least at
low depth (Figure 3). The best threshold depends on depth, though: QUAL ≥ 10 fixes most of the
low-depth problem but costs a little at 50x[^qual].

### Per sample

{{< figure src="per-sample-best-f1.png" alt="Best F1 per sample at each depth for each arm, with dnd samples shaded." caption="**Figure 4:** Best F1 for every sample at every depth, for SNPs and indels with hac and sup reads. F1 is on a logit scale and each panel has its own axis. A perfect score (F1 = 1) has no place on a logit scale, so perfect scores are drawn in their own column after the dotted line. The two shaded samples, *S. enterica* and *V. parahaemolyticus*, carry *dnd* phosphorothioate systems ([dorado#1599](https://github.com/nanoporetech/dorado/issues/1599)). Arm C + AF filter (0.65) is as in Figure 1." >}}

The pattern holds across samples (Figure 4). At sup 50x, Clair3 with the AF filter beats
Dorado on SNPs for 9 of the 14 samples and ties on 4. Clair3 beats Dorado on indels for 10 of
the 14 at 50x with either read model. Dorado's weakest indel results are *K. pneumoniae* and
*M. tuberculosis*.

There is a [known issue][dnd] where Dorado's bacterial model makes systematic errors in genomes
with *dnd* phosphorothioate modifications, such as *Salmonella enterica*. Our *S. enterica* and
*V. parahaemolyticus* samples have *dnd* systems, but they don't stand out here. That issue was
reported for reads basecalled with hac v6.0, and our reads are v4.3.0.

### Newer Clair3 and `lr:hq` change little

Arms A, B and C are almost indistinguishable in Figure 1. Moving from `map-ont` to `lr:hq`
changed median Best F1 by at most 0.0003. Moving from Clair3 1.0.5 to 2.0.3 with the same
(converted) models gave identical Best F1 for every sample, depth and read model. Clair3 2.0.3
is faster, though.

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

{{< figure src="runtime-memory.png" alt="Wall time and peak RAM of variant calling against depth for each arm, on log scales." caption="**Figure 5:** Wall time (left) and peak RAM (right) of variant calling against depth, both on log scales. Points are medians over the 28 read sets (14 samples, hac and sup) and bars show the range. Clair3 (Arms A-C) ran on 8 threads of an AMD EPYC 9745, and `dorado polish` (Arm D) on one NVIDIA H100 with 8 threads. The open marker is Dorado run on 8 CPU threads at 50x, for timing only. Alignment isn't shown. Peak RAM is host memory: Dorado's GPU memory isn't measured." >}}

On a GPU, Dorado is at least ten times faster than Clair3 at every depth (Figure 5). On CPU it
takes about as long, but needs much more memory. However, waiting in the queue on my HPC for a GPU took longer than the difference in time to CPU, so realistically, I would just use CPU unless you have instant access to an H100 and are *extremely* impatient (or need to call thousands of samples). Clair3 took *longer* at 5x and
10x (two to three minutes) than at 50x, and used more memory too. I haven't looked into why.
The full breakdown, including alignment, is in [Table 1](table1-runtime-memory.csv).

## Caveats

- **Only v4.3.0 reads.** These are the reads from the paper. Newer basecalling models give
  more accurate reads, and both callers may do better on them.
- **Clair3's bacterial model wasn't tested.** Clair3 now ships a model fine-tuned on bacteria
  (`r1041_e82_400bps_sup_v430_bacteria_finetuned`). It was [trained on 12 of our 14
  samples][clair3-ft], so testing it here would mean scoring it on its own training data.
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

- Clair3 is still the best overall, especially for indels.
- `dorado polish --vcf` is a reasonable choice for SNPs, particularly if you have a GPU
  and want speed. At 50x it makes a few more SNP errors per genome than Clair3. Its indels lag
  behind Clair3's.

> If you use `--haploid_precise`, consider running Clair3 diploid with an AF filter instead. It
> recovers the SNPs that `--haploid_precise` throws away, and costs nothing on indels. It gave
> the best SNP results in this benchmark at every depth.

> Don't trust Dorado's `PASS` filter at low depth: filter on QUAL (around 10 at 5–10x).

## Acknowledgements

Thanks to Ryan Wick, who got the ball rolling on this.

## Appendix

The [workflow][workflow], the aggregated tables and the figures are in the NanoVarBench
repository. The filtered VCFs for every arm and read set, and vcfdist's outputs for each, are
on Zenodo: [doi:10.5281/zenodo.23180742][zenodo].

{{< csv-table src="table-s1-per-sample.csv" caption="Table S1: Per-sample results for every arm, depth and read model, with actual depths" >}}

{{< share-file src="table-s1-per-sample.csv" >}}

{{< share-file src="table1-runtime-memory.csv" >}}

[^reads]: I didn't rebasecall the reads with the latest models, for three reasons. Keeping
    the paper's reads makes the results directly comparable with the paper. Dorado's `--bacteria` model supports
    reads basecalled with v4.2.0 or later, so v4.3.0 reads are within its range. And Ryan's
    [Dorado v2 polishing post][ryan-v2] found that the bacterial model did as well as or better
    than the newer models tied to specific basecallers, so rebasecalling was unlikely to change
    the answer.

[^depth]: Because of this, low-depth recall here isn't directly comparable with the paper's
    figures: at 5x the paper's random subsampling left more of the genome with very few reads.
    It is the same for every arm in this post.

[^any-bam]: Getting public FASTQs into `dorado polish` takes two changes. Dorado expects a BAM
    from `dorado aligner` with an `@RG` header line naming the basecalling model, and refuses
    anything else ("Input BAM file was not aligned using Dorado."). Reads downloaded from the
    SRA have neither. To use a minimap2 BAM, add a single `@RG` line with
    `DS:basecall_model=dna_r10.4.1_e8.2_400bps_hac@v4.3.0` (with `samtools reheader`), and pass
    the hidden `--any-bam` flag. Per-read `RG` tags aren't needed. I checked this against
    `dorado aligner` on one sample: the calls were identical, though the QUAL values of some
    records differed slightly.

[^gap]: At hac 10x, *K. pneumoniae* (791 misses), *K. variicola* (546) and *S. aureus*
    (341) account for 1,678 of Clair3's 2,478 misses, against 62, 20 and 3 for Dorado. The
    same three account for 71% of Clair3's misses at sup 10x. In these samples, Clair3's
    diploid model calls more true SNPs het even when nearly all reads carry the ALT: the het
    calls the AF filter rescues have a median AF of 0.8 to 0.9. These three are the samples
    whose names end in `__202310`, but I haven't worked out why they are affected more. The AF filter brings all three close to Dorado (109, 35 and 4
    misses).

[^qual]: Dorado's median indel F1 at fixed QUAL thresholds. At hac 5x: 0.419 with `PASS`
    only, 0.565 at QUAL ≥ 5, 0.755 at QUAL ≥ 10, and 0.796 at the best threshold. At hac 50x:
    0.973, 0.974, 0.966 and 0.978. For SNPs the default costs much less (hac 5x: 0.986 vs
    0.991).

[paper]: https://doi.org/10.7554/eLife.98300
[dorado-docs]: https://software-docs.nanoporetech.com/dorado/latest/secondary/polish/
[lrhq]: {{< ref "post/minimap2-lrhq-preset-testing" >}}
[ryan-v2]: https://rrwick.github.io/2026/06/19/dorado-v2-polishing.html
[workflow]: https://github.com/mbhall88/NanoVarBench/tree/main/updates/2026-dorado-polish
[truth]: https://zenodo.org/records/10867171
[zenodo]: https://doi.org/10.5281/zenodo.23180742
[rasusa]: https://github.com/mbhall88/rasusa
[af-script]: https://github.com/mbhall88/NanoVarBench/blob/main/updates/2026-dorado-polish/workflow/scripts/af_filter.py
[af-sweep]: https://github.com/mbhall88/NanoVarBench/blob/main/updates/2026-dorado-polish/final/tables/clair3_af_filter_summary.tsv
[clair3-ft]: https://github.com/HKU-BAL/Clair3/blob/19ddfed/docs/fine-tuning_Clair3_with_12_bacteria_samples.pdf
[dnd]: https://github.com/nanoporetech/dorado/issues/1599
