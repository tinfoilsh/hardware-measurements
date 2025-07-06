#!/bin/bash

rm -rf measurements/
mkdir -p measurements/

latest_commit=$(git rev-parse HEAD)

for dir in platforms/*; do
    name=$(basename $dir)
    echo "Measuring $name"
    ./dstack-mr measure $dir/metadata.json --cpu 32 --memory 100G --json-file measurements/${name}.${latest_commit}.json
done

# Combine all measurement files into one JSON, with platform names as keys
for file in measurements/*.json; do
    name=$(basename $file | cut -d. -f1)
    # Create a JSON with the platform name as the key
    jq --arg name "$name" '. as $data | {($name): $data}' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done

# # Merge all platform JSONs into a single file
jq -s 'reduce .[] as $item ({}; . * $item)' measurements/*.json > platform-measurements.json

rm -rf measurements/
