#!/usr/bin/env python3

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLATFORMS = json.loads((ROOT / "platform-inventory.json").read_text())


def qemu_shape(memory, topology):
    devices = [
        "e1000,netdev=net0,bus=pcie.0,addr=0x2,romfile=",
        "pci-testdev",
    ]
    devices.extend(
        f"virtio-scsi-pci,id=scsi{index},disable-legacy=on,iommu_platform=true"
        for index in range(topology["disks"])
    )

    fw_cfg = []
    profile = topology["profile"]
    if profile == "single":
        devices.append("pcie-root-port,id=pci.1,bus=pcie.0,slot=1,pref64-reserve=512G")
        devices.append("pci-testdev,bus=pci.1,addr=0x0")
    elif profile in ("blackwell", "hopper"):
        root_ports = 8 if profile == "blackwell" else 12
        for index in range(root_ports):
            port = 16 + index
            if index < 8:
                address = "0x16" if index == 0 else f"0x16.0x{index:x}"
            else:
                address = "0x17" if index == 8 else f"0x17.0x{index - 8:x}"
            multifunction = ",multifunction=on" if index in (0, 8) else ""
            devices.append(
                f"pcie-root-port,port={port},chassis={index + 1},id=pci.{index + 1},"
                f"bus=pcie.0{multifunction},addr={address}"
            )
            devices.append(f"pci-testdev,bus=pci.{index + 1},addr=0x0")
            if index < 8:
                fw_cfg.append(f"name=opt/ovmf/X-PciMmio64Mb{index + 1},string=262144")
    elif profile != "none":
        raise ValueError(f"unknown profile: {profile}")

    return {
        "machine": "q35,kernel_irqchip=split,memory-backend=mem0,smm=off,pic=off",
        "pci_hole64_start": topology.get("pci_hole64_start"),
        "pci_hole64_end": topology.get("pci_hole64_end"),
        "cpu": topology.get("cpu", "Skylake-Server,phys-bits=46"),
        "accel": "tcg",
        "globals": [
            f"q35-pcihost.pci-hole64-size={topology['pci_hole64_size']}",
            "vfio-pci.x-balloon-allowed=false",
            "vfio-pci.x-no-mmap=false",
        ],
        "objects": [f"memory-backend-memfd,id=mem0,size={memory},share=on"],
        "netdevs": ["hubport,id=net0,hubid=0"],
        "devices": devices,
        "fw_cfg": fw_cfg,
    }


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit(f"usage: {sys.argv[0]} PLATFORM OUTPUT_JSON [TRANSCRIPT]")

    name = sys.argv[1]
    output_json = Path(sys.argv[2]).resolve()
    transcript = Path(sys.argv[3]).resolve() if len(sys.argv) == 4 else None
    topology = PLATFORMS.get(name)
    if topology is None:
        raise SystemExit(f"missing topology for {name}")

    boot = {
        "cpus": topology["cpus"],
        "memory": topology["memory"],
        "bios": str((ROOT / "OVMF.fd").resolve()),
        "boot_order": str((ROOT / "boot" / "BootOrder.bin").resolve()),
        "path_boot_xxxx": f"{(ROOT / 'boot').resolve()}/",
    }
    metadata = {
        "boot_config": boot,
        "direct": {"kernel": "/dev/null", "initrd": "/dev/null", "cmdline": ""},
    }

    with tempfile.TemporaryDirectory(prefix=".measure-", dir=ROOT) as temporary:
        temporary_dir = Path(temporary)
        acpi_tables = temporary_dir / "acpi_tables.bin"
        generation_boot = dict(boot)
        generation_boot["memory"] = topology.get("acpi_memory", boot["memory"])
        generation_boot["qemu"] = qemu_shape(generation_boot["memory"], topology)
        generation_boot["acpi_tables"] = str(acpi_tables)
        generation_metadata = dict(metadata, boot_config=generation_boot)
        generation_path = temporary_dir / "generation.json"
        generation_path.write_text(json.dumps(generation_metadata, indent=2) + "\n")

        subprocess.run(
            [
                str(ROOT / "tdx-measure"),
                str(generation_path),
                "--platform-only",
                "--direct-boot",
                "true",
                "--create-acpi-tables",
                topology["qemu_source"],
                "--json-file",
                str(temporary_dir / "generation-measurement.json"),
            ],
            check=True,
        )

        digest = hashlib.sha256(acpi_tables.read_bytes()).hexdigest()
        if digest != topology["acpi_sha256"]:
            raise SystemExit(
                f"{name}: regenerated ACPI hash {digest} does not match reviewed "
                f"capture {topology['acpi_sha256']}"
            )

        boot["acpi_tables"] = str(acpi_tables)
        measurement_path = temporary_dir / "measurement.json"
        measurement_path.write_text(json.dumps(metadata, indent=2) + "\n")
        measurement_command = [
            str(ROOT / "tdx-measure"),
            str(measurement_path),
            "--platform-only",
            "--direct-boot",
            "true",
            "--json-file",
            str(output_json),
        ]
        if transcript is not None:
            measurement_command.extend(["--transcript", str(transcript)])
        subprocess.run(measurement_command, check=True)


if __name__ == "__main__":
    main()
