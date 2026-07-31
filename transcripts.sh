#!/bin/bash

set -ex

mkdir -p transcripts/
mkdir -p measurements/

for dir in platforms/*; do
    name=$(basename $dir)
    echo "Generating transcript for $name"
    ./measure-platform.py "$dir" "measurements/${name}.json" "transcripts/${name}.txt"
done

rm -rf measurements/
