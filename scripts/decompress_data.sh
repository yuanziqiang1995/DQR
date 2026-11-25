#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
find data -type f -name '*.gz' -print0 | while IFS= read -r -d '' file; do
    if [ ! -f "${file%.gz}" ]; then
        gzip -dk -- "$file"
    fi
done
echo "Data decompressed. The original .gz archives are preserved."
