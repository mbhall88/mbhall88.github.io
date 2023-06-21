---
layout: post
title: "Searching for shared sequence between <em>Mycobacterium tuberculosis</em> and <em>Homo sapiens</em>"
date: 2023-06-21
tags: [bioinformatics, shared-sequence, kmers, tuberculosis, human]
---

[TOC]: #

# Table of Contents
- [Motivation](#motivation)
- [References](#references)


# Motivation

We are in the early stages of planning a *Mycobacterium tuberculosis* (MTB) analysis pipeline for a research project in Papua New Guinea. We'll be sequencing sputum samples with Oxford Nanopore Technologies (ONT) devices and were thinking of different ways of decontaminating the data - i.e. remove anything non-MTB. Sputum samples traditionally have a lot of host (human) reads and reads from a variety of bacteria. Traditionally the MTB component is quite small<sup>1</sup>.


# References

1. Nilgiriwala K, Rabodoarivelo M-S, Hall MB, Patel G, Mandal A, Mishra S, et al. Genomic sequencing from sputum for tuberculosis disease diagnosis, lineage determination, and drug susceptibility prediction. J Clin Microbiol. 2023;61: e0157822. doi:[10.1128/jcm.01578-22](https://doi.org/10.1128/jcm.01578-22)