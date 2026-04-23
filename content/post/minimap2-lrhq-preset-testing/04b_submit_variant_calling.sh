#!/bin/bash
cd /scratch/user/uqmhal11/minimap_preset_testing/variants || exit 1

URI="docker://quay.io/mbhall88/clair3:1.0.5"
script="/scratch/user/uqmhal11/minimap_preset_testing/scripts/04a_clair3_wrapper.sh"
threads=8

for bam in ../alignments/*.bam; do
    filename=$(basename "$bam")
    base="${filename%.bam}"

    if [[ "$base" == *"_hac_"* ]]; then
        read_model="hac"
        sample="${base%%_hac_*}"
        preset="${base##*_hac_}"
    elif [[ "$base" == *"_sup_"* ]]; then
        read_model="sup"
        sample="${base%%_sup_*}"
        preset="${base##*_sup_}"
    else
        echo "Warning: Could not parse filename $filename. Skipping."
        continue
    fi

    outdir="${read_model}/${preset}/${sample}"
    mkdir -p "$outdir"

    ref="../data/truth_vcfs/${sample}/mutreference.fna"
    outvcf="${outdir}/${sample}.vcf.gz"
    log="${outdir}/${sample}.log"

    if [[ -f "$outvcf" ]]; then
        echo "Skipping variant calling: $outvcf already exists."
        continue
    fi

    clair_model="dna_r10.4.1_e8.2_400bps_${read_model}@v4.3.0"
    job_name="clair_${sample}_${read_model}_${preset}"

    echo "Submitting: $job_name -> Output to $outdir/"

    ssubmit -t 2h -m 16g "$job_name" \
        "apptainer exec $URI bash $script -b $bam -r $ref -o $outvcf -m $clair_model -v v4.3.0 -s $sample -t $threads -l $log" -- -c $threads
done
