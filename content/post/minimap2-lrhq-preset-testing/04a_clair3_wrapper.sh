#!/usr/bin/env bash
set -euo pipefail

threads=1
log_file=""

usage() {
    cat <<EOF
Usage: $(basename "$0") -b <bam> -r <ref> -o <outvcf> -m <model> -v <version> -s <sample> [-t <threads>] [-l <log>]

Required arguments:
    -b, --bam      Input alignment BAM file
    -r, --ref      Reference FASTA file
    -o, --outvcf   Output VCF file path
    -m, --model    Base model name (e.g., dna_r10.4.1_e8.2_400bps_sup@v4.3.0)
    -v, --version  Model version (e.g., v4.3.0)
    -s, --sample   Sample name

Optional arguments:
    -t, --threads  Number of threads to use (default: 1)
    -l, --log      Log file to redirect stdout and stderr
    -h, --help     Show this help message
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
    -b | --bam)
        aln="$2"
        shift 2
        ;;
    -r | --ref)
        ref="$2"
        shift 2
        ;;
    -o | --outvcf)
        outvcf="$2"
        shift 2
        ;;
    -m | --model)
        model="$2"
        shift 2
        ;;
    -v | --version)
        version="$2"
        shift 2
        ;;
    -s | --sample)
        sample="$2"
        shift 2
        ;;
    -t | --threads)
        threads="$2"
        shift 2
        ;;
    -l | --log)
        log_file="$2"
        shift 2
        ;;
    -h | --help) usage ;;
    *)
        echo "Error: Unknown parameter passed: $1"
        usage
        ;;
    esac
done

if [[ -z "${aln:-}" || -z "${ref:-}" || -z "${outvcf:-}" || -z "${model:-}" || -z "${version:-}" || -z "${sample:-}" ]]; then
    echo "Error: Missing required arguments."
    usage
fi

if [[ -n "$log_file" ]]; then
    exec &>"$log_file"
fi

model_name=$(echo "$model" | sed -E 's/.*dna_(.*)@.*/\1/')
model_name=$(echo "$model_name" | sed -E 's/\.//g')
model_name="${model_name}_${version}"
model_name=$(echo "$model_name" | sed -E 's/\.//g')

if [[ "$model" == *_fast@* ]]; then
    model_name=$(echo "$model_name" | sed -E 's/_fast/_hac/')
fi

model_path="/opt/models/${model_name}"
tmpoutdir=$(mktemp -d)
trap 'rm -rf "$tmpoutdir"' EXIT

echo "Running Clair3 with model: $model_path"

run_clair3.sh \
    --bam_fn="$aln" \
    --ref_fn="$ref" \
    --threads="$threads" \
    --platform="ont" \
    --model_path="$model_path" \
    --output="$tmpoutdir" \
    --sample_name="$sample" \
    --include_all_ctgs \
    --haploid_precise \
    --no_phasing_for_fa \
    --enable_long_indel

mv "${tmpoutdir}/merge_output.vcf.gz" "$outvcf"
