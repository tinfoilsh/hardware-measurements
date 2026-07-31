#!/bin/bash

set -ex

mkdir -p transcripts/
mkdir -p measurements/

while IFS= read -r name; do
    echo "Generating transcript for $name"
    ./measure-platform.py "$name" "measurements/${name}.json" "transcripts/${name}.txt"
done < <(jq -r 'keys[]' platform-inventory.json)

rm -rf measurements/
