#!/bin/bash

set -euo pipefail

repo=tinfoilsh/tdx-measure-tinfoil
version=v0.1.2-tinfoil.1
sha256=0b104e31e66179f4a96266eca7b425572f491611e9f42a72a8a1eb8244d29dd9

curl --fail --location --show-error --silent --retry 3 \
    "https://github.com/${repo}/releases/download/${version}/tdx-measure" \
    --output tdx-measure
echo "${sha256}  tdx-measure" | sha256sum --check --status
chmod +x tdx-measure
