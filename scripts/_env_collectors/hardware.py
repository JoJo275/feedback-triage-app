"""Physical hardware collector — CPU, GPU, RAM, storage devices, motherboard.

Collects detailed hardware specifications beyond what the system collector
provides.  Uses platform-specific commands (wmic/PowerShell on Windows,
/proc and lspci on Linux, system_profiler on macOS).
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


def _run_cmd(
    cmd: list[str], *, timeout: float = 10.0
) -> subprocess.CompletedProcess[str]:
    """Run a command safely, returning CompletedProcess."""
    return subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------


def _collect_cpu() -> dict[str, Any]:
    """Collect CPU information."""
    info: dict[str, Any] = {
        "architecture": platform.machine(),
        "physical_cores": None,
        "logical_cores": os.cpu_count(),
        "model": None,
        "vendor": None,
        "frequency_mhz": None,
        "cache_size": None,
        "features": [],
    }

    if sys.platform == "win32":
        _cpu_windows(info)
    elif sys.platform == "darwin":
        _cpu_macos(info)
    else:
        _cpu_linux(info)

    return info


def _cpu_windows(info: dict[str, Any]) -> None:
    """Populate CPU info on Windows via PowerShell/wmic."""
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_Processor | "
                    "Select-Object Name, Manufacturer, NumberOfCores, "
                    "NumberOfLogicalProcessors, MaxClockSpeed, L2CacheSize, "
                    "L3CacheSize | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, list):
                data = data[0]
            info["model"] = data.get("Name", "").strip()
            info["vendor"] = data.get("Manufacturer", "").strip()
            info["physical_cores"] = data.get("NumberOfCores")
            info["logical_cores"] = (
                data.get("NumberOfLogicalProcessors") or info["logical_cores"]
            )
            info["frequency_mhz"] = data.get("MaxClockSpeed")
            l2 = data.get("L2CacheSize", 0) or 0
            l3 = data.get("L3CacheSize", 0) or 0
            parts = []
            if l2:
                parts.append(f"L2: {l2} KB")
            if l3:
                parts.append(f"L3: {l3} KB")
            info["cache_size"] = ", ".join(parts) if parts else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass


def _cpu_linux(info: dict[str, Any]) -> None:
    """Populate CPU info on Linux via /proc/cpuinfo."""
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        return
    try:
        content = cpuinfo.read_text(encoding="utf-8", errors="replace")
        model = re.search(r"model name\s*:\s*(.+)", content)
        if model:
            info["model"] = model.group(1).strip()
        vendor = re.search(r"vendor_id\s*:\s*(.+)", content)
        if vendor:
            info["vendor"] = vendor.group(1).strip()
        cache = re.search(r"cache size\s*:\s*(.+)", content)
        if cache:
            info["cache_size"] = cache.group(1).strip()

        # Physical cores via unique core ids
        core_ids = set(re.findall(r"core id\s*:\s*(\d+)", content))
        physical_ids = set(re.findall(r"physical id\s*:\s*(\d+)", content))
        if core_ids and physical_ids:
            info["physical_cores"] = len(core_ids) * len(physical_ids)

        # CPU flags/features
        flags_match = re.search(r"flags\s*:\s*(.+)", content)
        if flags_match:
            all_flags = flags_match.group(1).strip().split()
            # Pick notable features only
            notable = {"sse4_2", "avx", "avx2", "avx512f", "aes", "vmx", "svm", "ht"}
            info["features"] = sorted(f for f in all_flags if f in notable)

        # Frequency
        mhz = re.search(r"cpu MHz\s*:\s*([\d.]+)", content)
        if mhz:
            info["frequency_mhz"] = round(float(mhz.group(1)))
    except OSError:
        pass


def _cpu_macos(info: dict[str, Any]) -> None:
    """Populate CPU info on macOS via sysctl."""
    try:
        result = _run_cmd(["sysctl", "-a"], timeout=5.0)
        if result.returncode == 0:
            content = result.stdout
            brand = re.search(r"machdep\.cpu\.brand_string:\s*(.+)", content)
            if brand:
                info["model"] = brand.group(1).strip()
            cores = re.search(r"hw\.physicalcpu:\s*(\d+)", content)
            if cores:
                info["physical_cores"] = int(cores.group(1))
            freq = re.search(r"hw\.cpufrequency:\s*(\d+)", content)
            if freq:
                info["frequency_mhz"] = int(freq.group(1)) // 1_000_000
    except (OSError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# GPU
# ---------------------------------------------------------------------------


def _collect_gpus() -> list[dict[str, Any]]:
    """Collect GPU information."""
    if sys.platform == "win32":
        return _gpus_windows()
    if sys.platform == "darwin":
        return _gpus_macos()
    return _gpus_linux()


def _gpus_windows() -> list[dict[str, Any]]:
    """Collect GPU info on Windows via PowerShell."""
    gpus: list[dict[str, Any]] = []
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object Name, AdapterCompatibility, DriverVersion, "
                    "AdapterRAM, VideoModeDescription, CurrentRefreshRate, "
                    "VideoProcessor, Status | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for gpu in data:
                adapter_ram = gpu.get("AdapterRAM")
                vram_mb = round(adapter_ram / (1024 * 1024)) if adapter_ram else None
                resolution = gpu.get("VideoModeDescription", "")
                gpus.append(
                    {
                        "name": (gpu.get("Name") or "").strip(),
                        "vendor": (gpu.get("AdapterCompatibility") or "").strip(),
                        "driver_version": (gpu.get("DriverVersion") or "").strip(),
                        "vram_mb": vram_mb,
                        "resolution": resolution.strip() if resolution else None,
                        "refresh_rate_hz": gpu.get("CurrentRefreshRate"),
                        "processor": (gpu.get("VideoProcessor") or "").strip() or None,
                        "status": (gpu.get("Status") or "").strip(),
                    }
                )
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return gpus


def _gpus_linux() -> list[dict[str, Any]]:
    """Collect GPU info on Linux via lspci."""
    gpus: list[dict[str, Any]] = []
    lspci = shutil.which("lspci")
    if not lspci:
        return gpus
    try:
        result = _run_cmd([lspci, "-v", "-s", ""], timeout=5.0)
        if result.returncode != 0:
            result = _run_cmd([lspci], timeout=5.0)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if any(
                    kw in line.lower() for kw in ("vga", "3d controller", "display")
                ):
                    # e.g. "01:00.0 VGA compatible controller: NVIDIA Corporation ..."
                    match = re.search(r":\s+(.+)", line)
                    name = match.group(1).strip() if match else line.strip()
                    gpus.append({"name": name, "source": "lspci"})
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Try nvidia-smi for more details
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = _run_cmd(
                [
                    nvidia_smi,
                    "--query-gpu=name,memory.total,driver_version,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                timeout=5.0,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        gpus.append(
                            {
                                "name": parts[0],
                                "vram_mb": int(parts[1])
                                if parts[1].isdigit()
                                else None,
                                "driver_version": parts[2],
                                "temperature_c": int(parts[3])
                                if parts[3].isdigit()
                                else None,
                                "source": "nvidia-smi",
                            }
                        )
        except (OSError, subprocess.TimeoutExpired):
            pass

    return gpus


def _gpus_macos() -> list[dict[str, Any]]:
    """Collect GPU info on macOS via system_profiler."""
    gpus: list[dict[str, Any]] = []
    try:
        result = _run_cmd(
            ["system_profiler", "SPDisplaysDataType"],
            timeout=10.0,
        )
        if result.returncode == 0:
            current: dict[str, Any] = {}
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("Chipset Model:"):
                    if current:
                        gpus.append(current)
                    current = {"name": stripped.split(":", 1)[1].strip()}
                elif "VRAM" in stripped and current:
                    current["vram"] = stripped.split(":", 1)[1].strip()
                elif "Vendor:" in stripped and current:
                    current["vendor"] = stripped.split(":", 1)[1].strip()
            if current:
                gpus.append(current)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return gpus


# ---------------------------------------------------------------------------
# RAM
# ---------------------------------------------------------------------------


def _collect_ram() -> dict[str, Any]:
    """Collect RAM information."""
    info: dict[str, Any] = {
        "total_gb": None,
        "available_gb": None,
        "used_percent": None,
        "type": None,
        "speed_mhz": None,
        "slots_used": None,
        "slots_total": None,
        "modules": [],
    }

    if sys.platform == "win32":
        _ram_windows(info)
    elif sys.platform == "darwin":
        _ram_macos(info)
    else:
        _ram_linux(info)

    return info


def _smbios_rank_list() -> list[int | None]:
    """Parse raw SMBIOS Type 17 entries to extract per-DIMM rank counts.

    WMI's ``Win32_PhysicalMemory.Rank`` is often null on consumer boards.
    The SMBIOS "Attributes" byte (offset 0x1B in a Type 17 structure,
    bits 0-3) reliably stores the number of ranks for populated DIMMs.

    Returns a list of rank values for each **populated** memory slot
    (i.e. entries where the Size field > 0), in SMBIOS enumeration order
    which matches the WMI module order.
    """
    # PowerShell script that reads raw SMBIOS and emits a JSON array of
    # rank values for populated Type 17 entries.
    ps_script = (
        "$b=(Get-CimInstance -Namespace root/WMI "
        "-ClassName MSSmBios_RawSMBiosTables).SMBiosData;"
        "$r=@();$i=0;"
        "while($i -lt $b.Length-4){"
        "$t=$b[$i];$l=$b[$i+1];"
        "if($t -eq 17 -and $l -ge 28){"
        "$sz=[BitConverter]::ToUInt16($b,$i+12);"
        "if($sz -gt 0){"
        "$a=$b[$i+27] -band 0x0F;"
        "$r+=$a"
        "}};"
        "$i+=$l;"
        "while($i -lt $b.Length-1){"
        "if($b[$i] -eq 0 -and $b[$i+1] -eq 0){$i+=2;break}$i++}};"
        "ConvertTo-Json @($r)"
    )
    try:
        result = _run_cmd(
            ["powershell", "-NoProfile", "-Command", ps_script],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, int):
                return [data]
            if isinstance(data, list):
                return [int(v) if v else None for v in data]
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return []


def _ram_windows(info: dict[str, Any]) -> None:
    """Populate RAM info on Windows."""
    # Total/available via os
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        info["total_gb"] = round(mem.ullTotalPhys / (1024**3), 1)
        info["available_gb"] = round(mem.ullAvailPhys / (1024**3), 1)
        info["used_percent"] = mem.dwMemoryLoad
    except (OSError, AttributeError):
        pass

    # Module details via PowerShell
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_PhysicalMemory | "
                    "Select-Object Capacity, Speed, ConfiguredClockSpeed, "
                    "MemoryType, SMBIOSMemoryType, Manufacturer, BankLabel, "
                    "FormFactor, PartNumber, DataWidth, Rank, "
                    "DeviceLocator | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            modules = []
            for mod in data:
                cap = mod.get("Capacity")
                size_gb = round(cap / (1024**3), 1) if cap else None
                smbios_type = mod.get("SMBIOSMemoryType", 0)
                mem_type_map = {
                    20: "DDR",
                    21: "DDR2",
                    24: "DDR3",
                    26: "DDR4",
                    34: "DDR5",
                }
                mem_type = mem_type_map.get(
                    smbios_type, f"Type {smbios_type}" if smbios_type else None
                )
                form_factor_code = mod.get("FormFactor", 0)
                form_factor_map = {
                    0: None,
                    8: "DIMM",
                    12: "SO-DIMM",
                }
                form_factor = form_factor_map.get(
                    form_factor_code,
                    f"FormFactor {form_factor_code}" if form_factor_code else None,
                )
                modules.append(
                    {
                        "size_gb": size_gb,
                        "speed_mhz": mod.get("Speed"),
                        "configured_speed_mhz": mod.get("ConfiguredClockSpeed"),
                        "type": mem_type,
                        "manufacturer": (mod.get("Manufacturer") or "").strip(),
                        "bank": (mod.get("BankLabel") or "").strip(),
                        "form_factor": form_factor,
                        "part_number": (mod.get("PartNumber") or "").strip() or None,
                        "data_width": mod.get("DataWidth"),
                        "ranks": mod.get("Rank"),
                        "device_locator": (mod.get("DeviceLocator") or "").strip()
                        or None,
                    }
                )
            info["modules"] = modules
            info["slots_used"] = len(modules)
            if modules:
                info["type"] = modules[0].get("type")
                info["speed_mhz"] = modules[0].get("speed_mhz")

            # Patch in rank data from raw SMBIOS (WMI Rank is often null)
            smbios_ranks = _smbios_rank_list()
            for idx, mod in enumerate(modules):
                if mod.get("ranks") is None and idx < len(smbios_ranks):
                    rank_val = smbios_ranks[idx]
                    mod["ranks"] = rank_val if rank_val else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    # Total slots
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "((Get-CimInstance Win32_PhysicalMemoryArray).MemoryDevices) | ConvertTo-Json",
            ],
            timeout=5.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            slots = json.loads(result.stdout)
            if isinstance(slots, int):
                info["slots_total"] = slots
            elif isinstance(slots, list):
                info["slots_total"] = sum(s for s in slots if isinstance(s, int))
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass


def _ram_linux(info: dict[str, Any]) -> None:
    """Populate RAM info on Linux via /proc/meminfo."""
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return
    try:
        content = meminfo.read_text(encoding="utf-8", errors="replace")
        total = re.search(r"MemTotal:\s+(\d+)\s+kB", content)
        avail = re.search(r"MemAvailable:\s+(\d+)\s+kB", content)
        if total:
            total_kb = int(total.group(1))
            info["total_gb"] = round(total_kb / (1024**2), 1)
        if avail:
            avail_kb = int(avail.group(1))
            info["available_gb"] = round(avail_kb / (1024**2), 1)
        if info["total_gb"] and info["available_gb"]:
            used = info["total_gb"] - info["available_gb"]
            info["used_percent"] = round((used / info["total_gb"]) * 100)
    except (OSError, ValueError):
        pass

    # Try dmidecode for module info (needs root, graceful fail)
    dmidecode = shutil.which("dmidecode")
    if dmidecode:
        try:
            result = _run_cmd([dmidecode, "-t", "memory"], timeout=5.0)
            if result.returncode == 0:
                speed_m = re.search(r"Speed:\s+(\d+)\s+MT/s", result.stdout)
                type_m = re.search(r"Type:\s+(DDR\d?)", result.stdout)
                if speed_m:
                    info["speed_mhz"] = int(speed_m.group(1))
                if type_m:
                    info["type"] = type_m.group(1)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _ram_macos(info: dict[str, Any]) -> None:
    """Populate RAM info on macOS."""
    try:
        result = _run_cmd(["sysctl", "hw.memsize"], timeout=5.0)
        if result.returncode == 0:
            match = re.search(r"(\d+)", result.stdout)
            if match:
                info["total_gb"] = round(int(match.group(1)) / (1024**3), 1)
    except (OSError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# Storage Devices
# ---------------------------------------------------------------------------


def _collect_storage() -> list[dict[str, Any]]:
    """Collect storage device information."""
    if sys.platform == "win32":
        return _storage_windows()
    if sys.platform == "darwin":
        return _storage_macos()
    return _storage_linux()


def _storage_windows() -> list[dict[str, Any]]:
    """Collect storage device info on Windows."""
    devices: list[dict[str, Any]] = []
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-PhysicalDisk | "
                    "Select-Object FriendlyName, MediaType, BusType, Size, "
                    "HealthStatus, OperationalStatus | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for disk in data:
                size = disk.get("Size")
                size_gb = round(size / (1024**3), 1) if size else None
                devices.append(
                    {
                        "name": (disk.get("FriendlyName") or "").strip(),
                        "type": (disk.get("MediaType") or "").strip() or "Unknown",
                        "bus": (disk.get("BusType") or "").strip(),
                        "size_gb": size_gb,
                        "health": (disk.get("HealthStatus") or "").strip(),
                        "status": (disk.get("OperationalStatus") or "").strip(),
                    }
                )
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    # Get logical drive info (free space)
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    'Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | '
                    "Select-Object DeviceID, Size, FreeSpace, FileSystem | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for drive in data:
                size = drive.get("Size")
                free = drive.get("FreeSpace")
                devices.append(
                    {
                        "name": f"Drive {drive.get('DeviceID', '?')}",
                        "type": "Logical Volume",
                        "filesystem": drive.get("FileSystem"),
                        "size_gb": round(size / (1024**3), 1) if size else None,
                        "free_gb": round(free / (1024**3), 1) if free else None,
                        "used_percent": round(((size - free) / size) * 100)
                        if size and free
                        else None,
                    }
                )
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    return devices


def _storage_linux() -> list[dict[str, Any]]:
    """Collect storage info on Linux via lsblk."""
    devices: list[dict[str, Any]] = []
    lsblk = shutil.which("lsblk")
    if lsblk:
        try:
            result = _run_cmd(
                [lsblk, "-Jbo", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,ROTA"],
                timeout=5.0,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json

                data = json.loads(result.stdout)
                for dev in data.get("blockdevices", []):
                    if dev.get("type") == "disk":
                        size = dev.get("size")
                        size_gb = round(int(size) / (1024**3), 1) if size else None
                        rota = dev.get("rota")
                        disk_type = (
                            "HDD"
                            if rota == "1"
                            else "SSD"
                            if rota == "0"
                            else "Unknown"
                        )
                        devices.append(
                            {
                                "name": dev.get("name", ""),
                                "model": (dev.get("model") or "").strip(),
                                "type": disk_type,
                                "size_gb": size_gb,
                            }
                        )
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass

    # Filesystem usage via df
    df_exe = shutil.which("df")
    if df_exe:
        try:
            result = _run_cmd(
                [df_exe, "-h", "--output=source,size,used,avail,pcent,fstype,target"],
                timeout=5.0,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()[1:]  # skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 7 and not parts[0].startswith("tmpfs"):
                        devices.append(
                            {
                                "name": parts[0],
                                "type": "Filesystem",
                                "filesystem": parts[5],
                                "size": parts[1],
                                "used": parts[2],
                                "free": parts[3],
                                "used_percent_str": parts[4],
                                "mount": parts[6],
                            }
                        )
        except (OSError, subprocess.TimeoutExpired):
            pass

    return devices


def _storage_macos() -> list[dict[str, Any]]:
    """Collect storage info on macOS."""
    devices: list[dict[str, Any]] = []
    try:
        result = _run_cmd(["diskutil", "list"], timeout=5.0)
        if result.returncode == 0:
            devices.extend(
                {"name": line.strip(), "type": "Disk"}
                for line in result.stdout.splitlines()
                if line.startswith("/dev/disk")
            )
    except (OSError, subprocess.TimeoutExpired):
        pass
    return devices


# ---------------------------------------------------------------------------
# Motherboard
# ---------------------------------------------------------------------------


def _collect_motherboard() -> dict[str, Any]:
    """Collect motherboard information."""
    info: dict[str, Any] = {
        "manufacturer": None,
        "product": None,
        "serial": None,
        "bios_vendor": None,
        "bios_version": None,
        "bios_date": None,
    }

    if sys.platform == "win32":
        _motherboard_windows(info)
    elif sys.platform == "darwin":
        _motherboard_macos(info)
    else:
        _motherboard_linux(info)

    return info


def _motherboard_windows(info: dict[str, Any]) -> None:
    """Populate motherboard info on Windows."""
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_BaseBoard | "
                    "Select-Object Manufacturer, Product, SerialNumber | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, list):
                data = data[0]
            info["manufacturer"] = (data.get("Manufacturer") or "").strip()
            info["product"] = (data.get("Product") or "").strip()
            info["serial"] = (data.get("SerialNumber") or "").strip()
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    # BIOS info
    try:
        result = _run_cmd(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_BIOS | "
                    "Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate | ConvertTo-Json"
                ),
            ],
            timeout=10.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            if isinstance(data, list):
                data = data[0]
            info["bios_vendor"] = (data.get("Manufacturer") or "").strip()
            info["bios_version"] = (data.get("SMBIOSBIOSVersion") or "").strip()
            raw_date = data.get("ReleaseDate", "")
            if raw_date and isinstance(raw_date, str) and len(raw_date) >= 10:
                info["bios_date"] = raw_date[:10]
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass


def _motherboard_linux(info: dict[str, Any]) -> None:
    """Populate motherboard info on Linux via /sys/class/dmi."""
    dmi = Path("/sys/class/dmi/id")
    if dmi.is_dir():
        mapping = {
            "board_vendor": "manufacturer",
            "board_name": "product",
            "board_serial": "serial",
            "bios_vendor": "bios_vendor",
            "bios_version": "bios_version",
            "bios_date": "bios_date",
        }
        for filename, key in mapping.items():
            fpath = dmi / filename
            if fpath.is_file():
                try:
                    val = fpath.read_text(encoding="utf-8", errors="replace").strip()
                    if val and val not in ("", "To Be Filled By O.E.M."):
                        info[key] = val
                except OSError:
                    pass


def _motherboard_macos(info: dict[str, Any]) -> None:
    """Populate motherboard info on macOS."""
    try:
        result = _run_cmd(
            ["system_profiler", "SPHardwareDataType"],
            timeout=10.0,
        )
        if result.returncode == 0:
            model = re.search(r"Model Name:\s*(.+)", result.stdout)
            if model:
                info["product"] = model.group(1).strip()
            mfr = re.search(r"Model Identifier:\s*(.+)", result.stdout)
            if mfr:
                info["manufacturer"] = mfr.group(1).strip()
    except (OSError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# Collector class
# ---------------------------------------------------------------------------


class HardwareCollector(BaseCollector):
    """Collect detailed physical hardware specifications."""

    name = "hardware"
    timeout = 30.0

    @property
    def tier(self) -> Any:  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        cpu = _collect_cpu()
        gpus = _collect_gpus()
        ram = _collect_ram()
        storage = _collect_storage()
        motherboard = _collect_motherboard()

        return {
            "cpu": cpu,
            "gpus": gpus,
            "gpu_count": len(gpus),
            "ram": ram,
            "storage_devices": storage,
            "motherboard": motherboard,
        }
