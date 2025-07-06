import os
import json
import yaml


def measure(
    bios_file: str,
    kernel_file: str,
    initrd_file: str,
    cmdline: str,
    cpus: int,
    memory: int,
) -> None:
    """
    Measure MRTD using dstack-mr.

    Args:
        bios_file (str): Path to the BIOS file
        kernel_file (str): Path to the kernel file
        initrd_file (str): Path to the initrd file
        cmdline (str): Kernel command line
        cpus (int): Number of CPUs to allocate
        memory (int): Amount of memory to allocate in GB
    """
    metadata = {
        "bios": bios_file,
        "kernel": kernel_file,
        "initrd": initrd_file,
        "cmdline": cmdline,
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f)

    os.system(
        f"RUST_LOG=debug ./dstack-mr measure metadata.json --cpu {cpus} --memory {memory}G"
    )

if __name__ == "__main__":
    with open("platform.yml", "r") as f:
        cfg = yaml.safe_load(f)

        for platform_name, platform_cfg in cfg.items():
            measure(
                bios_file=platform_cfg["bios"],
                kernel_file=platform_cfg["kernel"],
                initrd_file=platform_cfg["initrd"],
                cmdline=platform_cfg["cmdline"],
                cpus=platform_cfg["cpus"],
                memory=platform_cfg["memory"],
            )
