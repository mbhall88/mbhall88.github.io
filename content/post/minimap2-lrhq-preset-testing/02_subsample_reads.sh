#!/bin/bash
cd /scratch/user/uqmhal11/minimap_preset_testing/data/reads

csv_file="/scratch/user/uqmhal11/minimap_preset_testing/NanoVarBench/config/accessions.csv"
truth_dir="../truth_vcfs"

mkdir -p hac_subsampled sup_subsampled

seed=23867

tail -n +2 "$csv_file" | while IFS=, read -r sample species biosample pod5 illumina ont_simplex_fast ont_simplex_hac ont_simplex_sup ont_duplex_hac ont_duplex_sup assembly remainder; do

    fai_file="${truth_dir}/${sample}/reference.fna.fai"

    if [[ ! -f "$fai_file" ]]; then
        echo "Error: Index file $fai_file not found for $sample. Skipping."
        continue
    fi

    hac_in="hac/${ont_simplex_hac}_1.fastq.gz"
    hac_out="hac_subsampled/${sample}.fastq.gz"

    if [[ -f "$hac_in" ]]; then
        if [[ -f "$hac_out" ]]; then
            echo "Skipping HAC subsampling: $hac_out already exists."
        else
            echo "Subsampling HAC: $hac_in -> $hac_out (50x, using $fai_file)"
            rasusa reads "$hac_in" -c 50 -g "$fai_file" -o "$hac_out" -s "$seed"
        fi
    fi

    sup_in="sup/${ont_simplex_sup}_1.fastq.gz"
    sup_out="sup_subsampled/${sample}.fastq.gz"

    if [[ -f "$sup_in" ]]; then
        if [[ -f "$sup_out" ]]; then
            echo "Skipping SUP extraction: $sup_out already exists."
        else
            id_file="sup_subsampled/${sample}_read_ids.txt"

            echo "Step 1: Extracting read IDs to $id_file"
            seqkit seq -n "$hac_out" | cut -f 2 -d' ' >"$id_file"

            echo "Step 2: Extracting corresponding SUP reads to $sup_out"
            ssubmit -t 6h -m 32g "${sample}_sup_extract" "rg -zFf $id_file -A 3 --no-context-separator  $sup_in | gzip > $sup_out"
        fi
    fi
done

echo "Subsampling complete!"
