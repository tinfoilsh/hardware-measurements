#!/bin/bash
#
# Compute ACPI hash from a platform metadata.json file.
#
# The hash is computed as SHA256(table_loader || rsdp || acpi_tables),
# matching the order that Stage0 uses when building and hashing ACPI tables.
#
# Usage: ./compute-acpi-hash.sh <path-to-metadata.json>
#

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <metadata.json>"
    echo "Example: $0 platforms/small_0d_amd/metadata.json"
    exit 1
fi

METADATA_JSON="$1"

if [ ! -f "$METADATA_JSON" ]; then
    echo "Error: File not found: $METADATA_JSON"
    exit 1
fi

# Get the directory containing metadata.json (paths are relative to it)
METADATA_DIR=$(dirname "$METADATA_JSON")

# Extract file paths from metadata.json using jq
TABLE_LOADER=$(jq -r '.boot_config.table_loader' "$METADATA_JSON")
RSDP=$(jq -r '.boot_config.rsdp' "$METADATA_JSON")
ACPI_TABLES=$(jq -r '.boot_config.acpi_tables' "$METADATA_JSON")

# Construct full paths
TABLE_LOADER_PATH="$METADATA_DIR/$TABLE_LOADER"
RSDP_PATH="$METADATA_DIR/$RSDP"
ACPI_TABLES_PATH="$METADATA_DIR/$ACPI_TABLES"

# Verify files exist
for file in "$TABLE_LOADER_PATH" "$RSDP_PATH" "$ACPI_TABLES_PATH"; do
    if [ ! -f "$file" ]; then
        echo "Error: File not found: $file"
        exit 1
    fi
done

# Compute SHA256 of concatenated files (order: table_loader, rsdp, acpi_tables)
# This matches Stage0's ACPI hash computation order
ACPI_HASH=$(cat "$TABLE_LOADER_PATH" "$RSDP_PATH" "$ACPI_TABLES_PATH" | sha256sum | cut -d' ' -f1)

echo "$ACPI_HASH"

