# Tinfoil Hardware Measurements

This repository contains platform configs for the different hardware and confidential VM configurations trusted by the Tinfoil clients when verifying remote attestation reports.
These configs are used to derive offline measurements which are then published on a transparency log (Sigstore).
These measurements are then used to verify attestation reports provided by trusted computing environments.

## Structure

- `platform-inventory.json` - Complete CPU, memory, disk, QEMU, and PCI inventory
- `boot/` - Shared OVMF boot variables
- `measure.sh` - Script to generate hardware measurements for all platforms
- `measure-platform.py` - Reconstructs and verifies each platform's ACPI tables
- `fetch-tdx-measure.sh` - Downloads the checksum-pinned Tinfoil release
- `fetch-ovmf.sh` - Downloads the OVMF firmware

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

ACPI tables are not collected from a running CVM or checked into the
repository. `platform-inventory.json` is the sole per-platform source of truth.
`measure-platform.py` translates each entry into complete `tdx-measure`
metadata and the ordered QEMU device list used by `tinfoild`, then reconstructs
the tables with the pinned QEMU source. The generated table must match the
reviewed SHA-256 digest in the inventory before its measurement is accepted.

All retained platform definitions target production QEMU 10.1.0. The obsolete
QEMU 9.2.1 platform variants have been removed.

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
