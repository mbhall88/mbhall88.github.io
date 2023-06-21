---
layout: post
title: "Searching for shared sequence between <em>Mycobacterium tuberculosis</em> and <em>Homo sapiens</em>"
date: 2023-06-21
tags: [bioinformatics, shared-sequence, kmers, tuberculosis, human]
---

[TOC]: #

# Table of Contents
- [Motivation](#motivation)
- [Shared *k*-mer content](#shared-k-mer-content)
- [References](#references)


# Motivation

We are in the early stages of planning a *Mycobacterium tuberculosis* (MTB) analysis pipeline for a research project in Papua New Guinea. We'll be sequencing sputum samples with Oxford Nanopore Technologies (ONT) devices and were thinking of different ways of decontaminating the data - i.e. remove anything non-MTB. Sputum samples traditionally have a lot of host (human) reads and reads from a variety of bacteria. Traditionally the MTB component is quite small<sup>1</sup>. One component of this pipeline will to upload sequencing reads to a remote/cloud server. As human reads are not used in any analysis steps, and will need to be removed prior to making any data available, we thought we could simplify things by removing human data as the first step. Our idea was to align reads to the human genome and just remove anything that aligns. However, one concern with this approach was whether any MTB reads could be lost in the process. This effectively boils down to the question: **Do _Mycobacterium tuberculosis_ and _Homo sapiens_ share genomic sequence**? After a literature search, I was unable to find an answer - which seemed quite surprising. My suspicion is that most people just assume they do not. (Or my literature searching skills are poor.) So let's take a look.

# Shared *k*-mer content

The first thing I thought to check was whether there are shared *k*-mers between the two reference genomes for MTB and human. As an aside, after struggling to install/run multiple tools for this job I wrote a simple Rust program - [`skc`][skc] - to do this comparison.

The human genome used is the [Telomere-to-Telomere (T2T) Consortium CHM13 v2.0 assembly][chm13v2] (accession: [GCA_009914755.4](https://www.ncbi.nlm.nih.gov/assembly/GCA_009914755.4))<sup>2</sup>. The MTB reference genome used is H37Rv (accession: [NC_000962.3](https://www.ncbi.nlm.nih.gov/nuccore/NC_000962.3))<sup>3</sup>. In addition to the CHM13 human genome, I looked at the shared *k*-mer content between MTB and a collection of other closely- and distantly-related genomes to give some background expectations. The other genomes are:

- The previous human reference genome [GRCh38.p14 (hg38)](https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.40/)
- The *Mus musculus* (mouse) reference genome [GRCm39 (mm39)](https://www.ncbi.nlm.nih.gov/assembly/GCF_000001635.27/)
- The *Arabidopsis thaliana* (thale cress) reference genome [TAIR10.1](https://www.ncbi.nlm.nih.gov/assembly/GCF_000001735.4)
- The Human immunodeficiency virus 1 (HIV-1) reference genome [NC_001802.1](https://www.ncbi.nlm.nih.gov/nuccore/NC_001802.1)
- The *Escherichia coli* strain K-12 substr. MG1655 reference genome [ASM584v2](https://www.ncbi.nlm.nih.gov/assembly/GCF_000005845.2/)
- The *Mycobacterium avium subsp. hominissuis* strain OCU889s_P11_4s reference genome [NZ_CP018019.1](https://www.ncbi.nlm.nih.gov/nuccore/NZ_CP018019.1)

I ran `skc` with all *k* from 13 to 31 and plot the number of shared *k*-mers at each *k* for each of the genomes listed above.

![plot of shared k-mer counts for each genome](/assets/img/posts/shared-seq/shared-count.png)


# References

1. Nilgiriwala K, Rabodoarivelo M-S, Hall MB, Patel G, Mandal A, Mishra S, et al. Genomic sequencing from sputum for tuberculosis disease diagnosis, lineage determination, and drug susceptibility prediction. J Clin Microbiol. 2023;61: e0157822. doi:[10.1128/jcm.01578-22](https://doi.org/10.1128/jcm.01578-22)
2. Rhie A, Nurk S, Cechova M, Hoyt SJ, Taylor DJ, Altemose N, et al. The complete sequence of a human Y chromosome. bioRxiv. 2022. doi:[10.1101/2022.12.01.518724](https://doi.org/10.1101/2022.12.01.518724)
3. Cole ST, Brosch R, Parkhill J, Garnier T, Churcher C, Harris D, et al. Deciphering the biology of Mycobacterium tuberculosis from the complete genome sequence. Nature. 1998;393: 537–544. doi:[10.1038/31159](https://doi.org/10.1038/31159)

[skc]: https://github.com/mbhall88/skc
[chm13v2]: https://github.com/marbl/CHM13#t2t-chm13v20-t2t-chm13y