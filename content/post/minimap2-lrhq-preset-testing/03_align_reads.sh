#!/bin/bash
cd /scratch/user/uqmhal11/minimap_preset_testing

out_dir="alignments"
truth_dir="data/truth_vcfs"
reads_dir="data/reads"
threads=8

mkdir -p "$out_dir"

for hac_fq in ${reads_dir}/hac_subsampled/*.fastq.gz; do
    filename=$(basename "$hac_fq")
    sample="${filename%.fastq.gz}"
    ref="${truth_dir}/${sample}/mutreference.fna"
    sup_fq="${reads_dir}/sup_subsampled/${sample}.fastq.gz"

    if [[ ! -f "$ref" ]]; then
        echo "Error: Reference not found at $ref. Skipping."
        continue
    fi

    # HAC + map-ont
    if [[ ! -f "${out_dir}/${sample}_hac_map-ont.bam" ]]; then
        echo " Aligning HAC reads with map-ont preset..."
        minimap2 -t "$threads" --cs --MD -aLx map-ont "$ref" "$hac_fq" |
            samtools sort --write-index -@ "$threads" -o "${out_dir}/${sample}_hac_map-ont.bam"
    else
        echo " Skipping HAC map-ont: output already exists."
    fi

    # HAC + lr:hq
    if [[ ! -f "${out_dir}/${sample}_hac_lr-hq.bam" ]]; then
        echo " Aligning HAC reads with lr:hq preset..."
        minimap2 -t "$threads" --cs --MD -aLx lr:hq "$ref" "$hac_fq" |
            samtools sort --write-index -@ "$threads" -o "${out_dir}/${sample}_hac_lr-hq.bam"
    else
        echo " Skipping HAC lr:hq: output already exists."
    fi

    if [[ -f "$sup_fq" ]]; then
        # SUP + map-ont
        if [[ ! -f "${out_dir}/${sample}_sup_map-ont.bam" ]]; then
            echo " Aligning SUP reads with map-ont preset..."
            minimap2 -t "$threads" --cs --MD -aLx map-ont "$ref" "$sup_fq" |
                samtools sort --write-index -@ "$threads" -o "${out_dir}/${sample}_sup_map-ont.bam"
        else
            echo " Skipping SUP map-ont: output already exists."
        fi

        # SUP + lr:hq
        if [[ ! -f "${out_dir}/${sample}_sup_lr-hq.bam" ]]; then
            echo " Aligning SUP reads with lr:hq preset..."
            minimap2 -t "$threads" --cs --MD -aLx lr:hq "$ref" "$sup_fq" |
                samtools sort --write-index -@ "$threads" -o "${out_dir}/${sample}_sup_lr-hq.bam"
        else
            echo " Skipping SUP lr:hq: output already exists."
        fi
    else
        echo " Warning: No SUP reads found for $sample."
    fi
done
