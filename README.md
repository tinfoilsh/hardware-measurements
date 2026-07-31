# Tinfoil Hardware Measurements

This repository reproducibly generates the TDX platform measurements trusted
by Tinfoil clients. ACPI tables are reconstructed offline; no running CVM or
ACPI endpoint is required.

## Repository layout

- `platform.json` contains the inputs for every supported VM shape.
- `toolchain.lock.json` pins `tdx-measure` and OVMF by URL and SHA-256.
- `boot/` contains the shared OVMF boot variables.
- `measure.py` reconstructs ACPI and generates the measurements.

All current platforms use QEMU 10.1.0.

## Generate measurements

Generate every platform:

```bash
./measure.py
```

Generate one or more platforms:

```bash
./measure.py medium_1d_new extra_large_2d_new
```

Use `--output` to change the output path. The default is
`hardware-measurements.json`.

## Add a platform

1. Copy the closest entry in `platform.json` and give it a unique name.
2. Set the production VM inputs:
   - `cpus` and `memory` are the guest CPU and memory values.
   - `disks` is the total number of SCSI controllers: three base disks plus
     the model disks. For example, a `2d` shape uses `5`.
   - `profile` selects the QEMU device topology: `none`, `single`, `hopper`, or
     `blackwell`.
   - `pci_hole64_size`, and when needed `pci_hole64_start` or
     `pci_hole64_end`, must match the production QEMU PCI aperture.
   - `qemu_source` must match the production QEMU version.
   - `acpi_memory` may use a smaller sparse backing size for ACPI generation;
     it does not change the guest memory encoded in the final measurement.
3. If the device topology is new, update `qemu_shape()` in `measure.py` to
   reproduce the ordered QEMU arguments used by `tinfoild`.
4. Generate the new platform locally:

   ```bash
   ./measure.py new_platform
   ```

5. Review the platform inputs and generated MRTD/RTMR0. After the shape is
   deployed, compare them with the live enclave attestation before publishing
   a hardware-measurements release.

The platform inputs and pinned toolchain are the auditable source of truth.
Generated ACPI tables and intermediate transcripts are intentionally not
checked in.

## Releases

Pull requests regenerate every platform. Tag pushes additionally publish
`hardware-measurements.json`, its hash, and a Sigstore attestation as release
assets. Do not create a tag until the generated measurements have been
reviewed against production.
