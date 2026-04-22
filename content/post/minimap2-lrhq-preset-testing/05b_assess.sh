#!/bin/bash
set -euo pipefail

filter_vcf=$1
truth_vcf=$2
ref=$3
bed=$4
outdir=$5
sample=$6

max_indel=50
log_file="${outdir}/${sample}_assess.log"

exec 2>"$log_file"
echo "Assessing variants for $sample..."

MAX_QUAL=$(bgzip -dc "$filter_vcf" | grep -v '^#' | cut -f 6 | sort -gr | sed -n '1p')
MAX_QUAL=${MAX_QUAL:-100}

vcfdist \
    "$filter_vcf" \
    "$truth_vcf" \
    "$ref" \
    --largest-variant "$max_indel" \
    --credit-threshold 1.0 \
    -p "${outdir}/${sample}." \
    -b "$bed" \
    -mx "$MAX_QUAL"

echo "Assessment complete!"
