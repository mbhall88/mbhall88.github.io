#!/bin/bash
set -euo pipefail

vcf=$1
ref=$2
faidx=$3
filter_script=$4
outdir=$5
sample=$6

max_indel=50
filter_vcf="${outdir}/${sample}.filter.vcf.gz"
log_file="${outdir}/${sample}_filter.log"

exec 2>"$log_file"

echo "Filtering variants for $sample..."

contigs=$(mktemp).contigs.txt
header=$(mktemp).header.txt
trap 'rm -f "$contigs" "$header"' EXIT

awk '{print "##contig=<ID="$1",length="$2">"}' "$faidx" >"$contigs"
(bcftools view -h "$vcf" |
    grep -v "^##contig=" |
    sed -e "3r $contigs") >"$header"

(bcftools reheader -h "$header" "$vcf" |
    python "$filter_script" |
    bcftools view -i 'GT="alt"' |
    bcftools view -e 'ALT="."' |
    bcftools norm -f "$ref" -a -c e -m - |
    bcftools norm -aD |
    bcftools filter -e "abs(ILEN)>${max_indel} || ALT=\"*\"" |
    bcftools +setGT - -- -t a -n c:M |
    bcftools sort |
    bcftools view -i 'GT="A"' -o "$filter_vcf")

bcftools index -f "$filter_vcf"
echo "Filtering complete!"
