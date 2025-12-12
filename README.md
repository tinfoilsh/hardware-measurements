# Tinfoil Hardware Measurements

This repository contains platform configs for the different hardware and confidential VM configurations trusted by the Tinfoil clients when verifying remote attestation reports.
These configs are used to derive offline measurements which are then published on a transparency log (Sigstore).
These measurements are then used to verify attestation reports provided by trusted computing environments.

## Structure

- `platforms/` - Contains platform-specific configurations and metadata
- `measure.sh` - Script to generate hardware measurements for all platforms
- `fetch-tdx-measure.sh` - Downloads the tdx-measure tool
- `fetch-ovmf.sh` - Downloads the OVMF firmware
- `analyze.py` - Utility to compare metadata files across platform configs

## Usage

1. Fetch required tools:
   ```bash
   ./fetch-tdx-measure.sh
   ./fetch-ovmf.sh
   ```

2. Generate measurements:
   ```bash
   ./measure.sh
   ```

## Platforms

Each platform directory contains:
- `metadata.json` - Configuration file with hardware specifications
- `metadata/` - Binary files with platform-specific data

## Output

Running `./measure.sh` generates `hardware-measurements.json` which contains the measurements for all platforms.

## GitHub Actions

This repository uses GitHub Actions to automatically generate and publish hardware measurements when new tags are pushed.

On each tag push:
1. The workflow downloads the required tools (`tdx-measure` and `OVMF`)
2. Generates hardware measurements for all platforms
3. Creates an attestation using Sigstore for the `hardware-measurements.json` file
4. Publishes the measurements and attestation as release assets

The attestation provides cryptographic proof of the measurement generation process and is published to Sigstore's transparency log, ensuring the integrity and provenance of the measurements.
