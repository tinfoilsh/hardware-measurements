#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <measurement_a> <measurement_b>"
    exit 1
fi

measurement_a=$1
measurement_b=$2

for f in acpi_tables.bin Boot0000.bin BootOrder.bin rsdp.bin table_loader.bin; do
    file_a=platforms/$measurement_a/metadata/$f
    file_b=platforms/$measurement_b/metadata/$f
    diff $file_a $file_b && echo "$f ok"
done
