# minimap2 Preset Performance Summary

*Values represent the mean across all tested samples at the 'BEST' threshold.*

| Variant Type   | Read Model   | Preset   | Mean Precision   | Mean Recall   | Mean F1 Score   |   Mean F1 Q-Score |
|:---------------|:-------------|:---------|:-----------------|:--------------|:----------------|------------------:|
| SNP            | hac          | lr-hq    | 99.997%          | 99.790%       | 99.892%         |             45.46 |
| SNP            | hac          | map-ont  | 99.995%          | 99.790%       | 99.891%         |             45.27 |
| SNP            | sup          | lr-hq    | 99.998%          | 99.795%       | 99.895%         |             50.97 |
| SNP            | sup          | map-ont  | 99.999%          | 99.785%       | 99.891%         |             50.74 |
| INDEL          | hac          | lr-hq    | 99.440%          | 97.697%       | 98.556%         |             24.48 |
| INDEL          | hac          | map-ont  | 99.421%          | 97.646%       | 98.521%         |             24.37 |
| INDEL          | sup          | lr-hq    | 99.980%          | 98.594%       | 99.281%         |             22.05 |
| INDEL          | sup          | map-ont  | 99.968%          | 98.581%       | 99.268%         |             21.89 |
| ALL            | hac          | lr-hq    | 99.985%          | 99.739%       | 99.861%         |             32.79 |
| ALL            | hac          | map-ont  | 99.983%          | 99.738%       | 99.860%         |             32.65 |
| ALL            | sup          | lr-hq    | 99.997%          | 99.770%       | 99.882%         |             35.16 |
| ALL            | sup          | map-ont  | 99.997%          | 99.761%       | 99.878%         |             34.94 |
