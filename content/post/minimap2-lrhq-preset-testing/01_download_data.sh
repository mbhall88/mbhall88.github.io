#!/bin/bash
set -euo pipefail

# Download and extract truth VCFs
cd /scratch/user/uqmhal11/minimap_preset_testing/data/truth_vcfs
wget -O truth_vcfs.zip "https://zenodo.org/api/records/10867171/files-archive"
unzip truth_vcfs.zip -d .
rm truth_vcfs.zip

for archive in *.tar.gz; do
    tar -xzf "$archive"
    rm "$archive"
done

# Create list of accessions to download
cd /scratch/user/uqmhal11/minimap_preset_testing/data/reads
csvtk cut -Uf ont_simplex_hac ../../config/accessions.csv >hac_accessions.txt
csvtk cut -Uf ont_simplex_sup ../../config/accessions.csv >sup_accessions.txt

# Download reads
ssubmit -t 12h -m 8g download_hac "kingfisher get --run-identifiers-list hac_accessions.txt -m ena-ascp ena-ftp --output-directory hac --check-md5sums"
ssubmit -t 12h -m 8g download_sup "kingfisher get --run-identifiers-list sup_accessions.txt -m ena-ascp ena-ftp --output-directory sup --check-md5sums"
