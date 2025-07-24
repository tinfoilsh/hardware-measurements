#!/bin/bash

set -ex

repo=virtee/tdx-measure

# Get latest release
latest_release=$(curl -s https://api.github.com/repos/$repo/releases/latest | grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4)

# Download the binary
curl -L https://github.com/$repo/releases/download/$latest_release/tdx-measure -o tdx-measure
chmod +x tdx-measure

if [ ! -f tdx-measure ]; then
    echo "tdx-measure binary not found"
    exit 1
fi
