#!/bin/bash

set -euo pipefail

repo=https://github.com/virtee/tdx-measure.git
revision=f083e5c4b3de5a1c447d04f26762c24686fe9ca4

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

git -C "$workdir" init --quiet
git -C "$workdir" remote add origin "$repo"
git -C "$workdir" fetch --quiet --depth 1 origin "$revision"
git -C "$workdir" checkout --quiet FETCH_HEAD
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -e CARGO_HOME=/tmp/cargo \
    -v "$workdir:/work" \
    -w /work \
    rust:1.88-bookworm@sha256:af306cfa71d987911a781c37b59d7d67d934f49684058f96cf72079c3626bfe0 \
    sh -c 'export PATH=/usr/local/cargo/bin:$PATH; cargo build --locked --release --manifest-path cli/Cargo.toml'
cp "$workdir/cli/target/release/tdx-measure" ./tdx-measure
