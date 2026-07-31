# Tinfoil Hardware Measurements

This repository contains platform configs for the different hardware and confidential VM configurations trusted by the Tinfoil clients when verifying remote attestation reports.
These configs are used to derive offline measurements which are then published on a transparency log (Sigstore).
These measurements are then used to verify attestation reports provided by trusted computing environments.

## Structure

- `platforms/` - Contains platform-specific configurations and metadata
- `measure.sh` - Script to generate hardware measurements for all platforms
- `measure-platform.py` - Reconstructs and verifies each platform's ACPI tables
- `platform-topologies.json` - Reviewed QEMU source, disk, and PCI topology inputs
- `fetch-tdx-measure.sh` - Builds the pinned tdx-measure revision
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
- `metadata/` - Boot variables used by OVMF

ACPI tables are not collected from a running CVM or checked into the
repository. `measure-platform.py` translates each entry in
`platform-topologies.json` into the ordered QEMU device list used by
`tinfoild`, then asks `tdx-measure` to reconstruct the tables with the pinned
QEMU source. The generated table must match the reviewed SHA-256 digest in the
topology manifest before its measurement is accepted.

The offline model uses deterministic stand-ins for devices whose runtime
arguments contain host-specific values:

- `pci-testdev` occupies the same PCI slot as the vsock device.
- A sparse `memory-backend-memfd` exposes the production guest-memory size to
  QEMU without requiring CI runners to commit that much host RAM.
- GPU endpoints are represented behind the same root ports; the reviewed PCI
  hole size captures their BAR allocation, including the larger B300 window.
- Disk controller count includes the root, config, and external-config disks,
  plus the model disks encoded by names such as `2d`.

## Output

Running `./measure.sh` generates `hardware-measurements.json` which contains the measurements for all platforms.

## GitHub Actions

Pull requests regenerate every platform and verify the reviewed ACPI digests.
Tag pushes additionally publish the resulting measurements.

On each tag push:
1. The workflow downloads the required tools (`tdx-measure` and `OVMF`)
2. Generates hardware measurements for all platforms
3. Creates an attestation using Sigstore for the `hardware-measurements.json` file
4. Publishes the measurements and attestation as release assets

The attestation provides cryptographic proof of the measurement generation process and is published to Sigstore's transparency log, ensuring the integrity and provenance of the measurements.
