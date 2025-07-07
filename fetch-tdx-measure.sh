#!/bin/bash

repo=tinfoilsh/tdx-measure

# Get latest release
latest_release=$(curl -s https://api.github.com/repos/$repo/releases/latest | grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4)

# Download the binary
curl -L https://github.com/$repo/releases/download/$latest_release/tdx-measure -o tdx-measure
chmod +x tdx-measure
