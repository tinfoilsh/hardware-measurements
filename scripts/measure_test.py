#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import measure


class MeasurementPlatformsTest(unittest.TestCase):
    def test_adds_v011_variant_without_changing_legacy_platform(self):
        platforms = measure.measurement_platforms()

        self.assertEqual(platforms["medium_1d_new"], measure.PLATFORMS["medium_1d_new"])
        self.assertEqual(platforms["medium_1d_v011"]["topology"], "v0.11")
        self.assertEqual(
            platforms["medium_1d_v011"]["tdx_measure"], "tdx_measure_v011"
        )

    def test_covers_cpu_only_fleet_shapes(self):
        platforms = measure.measurement_platforms()

        expected = {
            "small_0d_new": (8, "16384M", 3),
            "small_0d_v011": (8, "16384M", 3),
            "small_0d_32gb_new": (8, "32768M", 3),
            "small_0d_32gb_v011": (8, "32768M", 3),
            "tiny_0d_new": (2, "2048M", 3),
            "tiny_0d_v011": (2, "2048M", 3),
            "tiny_0d_5disk_new": (2, "2048M", 5),
            "tiny_0d_5disk_v011": (2, "2048M", 5),
            "medium_1d_cpu_new": (16, "65536M", 4),
            "medium_1d_cpu_v011": (16, "65536M", 4),
        }
        for name, shape in expected.items():
            platform = platforms[name]
            self.assertEqual(
                (platform["cpus"], platform["memory"], platform["disks"]), shape
            )

    def test_v011_fixed_virtio_topology(self):
        shape = measure.qemu_shape(
            "65536M", measure.measurement_platforms()["medium_1d_v011"]
        )

        self.assertEqual(
            shape["devices"][:6],
            [
                "virtio-serial-pci,bus=pcie.0,addr=0x1,disable-legacy=on,iommu_platform=true,romfile=",
                "virtio-net-pci,netdev=net0,bus=pcie.0,addr=0x2,disable-legacy=on,iommu_platform=true,romfile=",
                "virtio-blk-pci,drive=disk0,id=blk0,bus=pcie.0,addr=0x4,disable-legacy=on,iommu_platform=true,romfile=",
                "virtio-blk-pci,drive=disk1,id=blk1,bus=pcie.0,addr=0x5,disable-legacy=on,iommu_platform=true,romfile=",
                "virtio-blk-pci,drive=disk2,id=blk2,bus=pcie.0,addr=0x6,disable-legacy=on,iommu_platform=true,romfile=",
                "virtio-blk-pci,drive=disk3,id=blk3,bus=pcie.0,addr=0x7,disable-legacy=on,iommu_platform=true,romfile=",
            ],
        )
        self.assertEqual(
            shape["drives"],
            [
                "file=/dev/null,if=none,id=disk0,format=raw,readonly=on",
                "file=/dev/null,if=none,id=disk1,format=raw,readonly=on",
                "file=/dev/null,if=none,id=disk2,format=raw,readonly=on",
                "file=/dev/null,if=none,id=disk3,format=raw,readonly=on",
            ],
        )
        self.assertEqual(
            shape["fw_cfg"], ["name=opt/ovmf/X-PciMmio64Mb,string=262144"]
        )


if __name__ == "__main__":
    unittest.main()
