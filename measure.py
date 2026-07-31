#!/usr/bin/env python3

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLATFORMS = json.loads((ROOT / "platform.json").read_text())

TDX_MEASURE_URL = (
    "https://github.com/tinfoilsh/tdx-measure-tinfoil/releases/download/"
    "v0.1.2-tinfoil.1/tdx-measure"
)
TDX_MEASURE_SHA256 = "0b104e31e66179f4a96266eca7b425572f491611e9f42a72a8a1eb8244d29dd9"
OVMF_PACKAGE_URL = (
    "https://archive.ubuntu.com/ubuntu/pool/main/e/edk2/"
    "ovmf_2025.02-3ubuntu2_all.deb"
)
OVMF_SHA256 = "9e807cb2cd4313406a3aa4becc0836671a5c64ca7bdc08a45e15260184b446bf"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, destination):
    temporary = destination.with_suffix(destination.suffix + ".download")
    request = urllib.request.Request(url, headers={"User-Agent": "hardware-measurements"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            temporary.replace(destination)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def ensure_tdx_measure():
    binary = ROOT / "tdx-measure"
    if not binary.exists() or sha256(binary) != TDX_MEASURE_SHA256:
        print("Fetching tdx-measure v0.1.2-tinfoil.1", flush=True)
        download(TDX_MEASURE_URL, binary)
    if sha256(binary) != TDX_MEASURE_SHA256:
        raise SystemExit("tdx-measure checksum mismatch")
    binary.chmod(binary.stat().st_mode | 0o111)
    return binary


def ensure_ovmf():
    ovmf = ROOT / "OVMF.fd"
    if ovmf.exists() and sha256(ovmf) == OVMF_SHA256:
        return ovmf

    print("Fetching OVMF.fd", flush=True)
    with tempfile.TemporaryDirectory(prefix="ovmf-") as temporary:
        temporary_dir = Path(temporary)
        package = temporary_dir / "ovmf.deb"
        extracted = temporary_dir / "extracted"
        staged_ovmf = temporary_dir / "OVMF.fd"
        download(OVMF_PACKAGE_URL, package)
        subprocess.run(["dpkg-deb", "--extract", str(package), str(extracted)], check=True)
        shutil.copyfile(extracted / "usr/share/ovmf/OVMF.fd", staged_ovmf)
        if sha256(staged_ovmf) != OVMF_SHA256:
            raise SystemExit("OVMF.fd checksum mismatch")
        local_staging = ovmf.with_suffix(ovmf.suffix + ".download")
        shutil.copyfile(staged_ovmf, local_staging)
        local_staging.replace(ovmf)

    return ovmf


def qemu_shape(memory, platform):
    devices = [
        "e1000,netdev=net0,bus=pcie.0,addr=0x2,romfile=",
        "pci-testdev",
    ]
    devices.extend(
        f"virtio-scsi-pci,id=scsi{index},disable-legacy=on,iommu_platform=true"
        for index in range(platform["disks"])
    )

    fw_cfg = []
    profile = platform["profile"]
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
        "pci_hole64_start": platform.get("pci_hole64_start"),
        "pci_hole64_end": platform.get("pci_hole64_end"),
        "cpu": platform.get("cpu", "Skylake-Server,phys-bits=46"),
        "accel": "tcg",
        "globals": [
            f"q35-pcihost.pci-hole64-size={platform['pci_hole64_size']}",
            "vfio-pci.x-balloon-allowed=false",
            "vfio-pci.x-no-mmap=false",
        ],
        "objects": [f"memory-backend-memfd,id=mem0,size={memory},share=on"],
        "netdevs": ["hubport,id=net0,hubid=0"],
        "devices": devices,
        "fw_cfg": fw_cfg,
    }


def measure_platform(name, platform, tdx_measure, ovmf):
    boot = {
        "cpus": platform["cpus"],
        "memory": platform["memory"],
        "bios": str(ovmf),
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
        generation_boot["memory"] = platform.get("acpi_memory", boot["memory"])
        generation_boot["qemu"] = qemu_shape(generation_boot["memory"], platform)
        generation_boot["acpi_tables"] = str(acpi_tables)
        generation_metadata = dict(metadata, boot_config=generation_boot)
        generation_path = temporary_dir / "generation.json"
        generation_path.write_text(json.dumps(generation_metadata, indent=2) + "\n")

        subprocess.run(
            [
                str(tdx_measure),
                str(generation_path),
                "--platform-only",
                "--direct-boot",
                "true",
                "--create-acpi-tables",
                platform["qemu_source"],
                "--json-file",
                str(temporary_dir / "generation-measurement.json"),
            ],
            check=True,
        )

        digest = sha256(acpi_tables)
        if digest != platform["acpi_sha256"]:
            raise SystemExit(
                f"{name}: regenerated ACPI hash {digest} does not match reviewed "
                f"capture {platform['acpi_sha256']}"
            )

        boot["acpi_tables"] = str(acpi_tables)
        measurement_path = temporary_dir / "measurement.json"
        measurement_path.write_text(json.dumps(metadata, indent=2) + "\n")
        result_path = temporary_dir / "result.json"
        subprocess.run(
            [
                str(tdx_measure),
                str(measurement_path),
                "--platform-only",
                "--direct-boot",
                "true",
                "--json-file",
                str(result_path),
            ],
            check=True,
        )
        return json.loads(result_path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("platforms", nargs="*", help="platforms to measure; defaults to all")
    parser.add_argument("--output", default="hardware-measurements.json")
    args = parser.parse_args()

    names = args.platforms or sorted(PLATFORMS)
    unknown = sorted(set(names) - set(PLATFORMS))
    if unknown:
        parser.error(f"unknown platform: {', '.join(unknown)}")

    tdx_measure = ensure_tdx_measure()
    ovmf = ensure_ovmf()
    measurements = {}
    for name in names:
        print(f"Measuring {name}")
        measurements[name] = measure_platform(name, PLATFORMS[name], tdx_measure, ovmf)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(measurements, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
