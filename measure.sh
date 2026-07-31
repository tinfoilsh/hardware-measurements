#!/bin/bash

set -ex

rm -rf measurements/
mkdir -p measurements/

while IFS= read -r name; do
    echo "Measuring $name"
    ./measure-platform.py "$name" "measurements/${name}.json"
done < <(jq -r 'keys[]' platform-inventory.json)

# Combine all measurement files into one JSON, with platform names as keys
for file in measurements/*.json; do
    name=$(basename $file | cut -d. -f1)
    # Create a JSON with the platform name as the key
    jq --arg name "$name" '. as $data | {($name): $data}' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done

# # Merge all platform JSONs into a single file
jq -s 'reduce .[] as $item ({}; . * $item)' measurements/*.json > hardware-measurements.json

rm -rf measurements/
