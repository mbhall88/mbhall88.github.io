#!/bin/bash
cd /scratch/user/uqmhal11/minimap_preset_testing/variants || exit 1

filter_bash="/scratch/user/uqmhal11/minimap_preset_testing/scripts/05a_filter.sh"
assess_bash="/scratch/user/uqmhal11/minimap_preset_testing/scripts/05b_assess.sh"
filter_py="/scratch/user/uqmhal11/minimap_preset_testing/scripts/filter_hets.py"
truth_base="../data/truth_vcfs"

find . -mindepth 4 -maxdepth 4 -name "*.vcf.gz" | grep -v "\.filter\.vcf\.gz" | while read -r vcf; do
    vcf_clean=${vcf#./}
    read_model=$(echo "$vcf_clean" | cut -d'/' -f1)
    preset=$(echo "$vcf_clean" | cut -d'/' -f2)
    sample=$(echo "$vcf_clean" | cut -d'/' -f3)

    outdir=$(dirname "$vcf")
    ref="${truth_base}/${sample}/mutreference.fna"
    faidx="${ref}.fai"
    truth_vcf="${truth_base}/${sample}/truth.vcf.gz"
    bed="${truth_base}/${sample}/${sample}.bed"
    filter_vcf="${outdir}/${sample}.filter.vcf.gz"

    # skip submitting a job if the output already exists
    if [[ -f "$filter_vcf" ]]; then
        echo "Output $filter_vcf already exists, skipping $vcf"
        continue
    fi

    job_name="eval_${sample}_${read_model}_${preset}"

    ssubmit -t 1h -m 4g "$job_name" \
        "bash $filter_bash $vcf $ref $faidx $filter_py $outdir $sample && bash $assess_bash $filter_vcf $truth_vcf $ref $bed $outdir $sample"
done
