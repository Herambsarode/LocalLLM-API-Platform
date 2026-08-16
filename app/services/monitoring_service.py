import psutil
import time
from typing import Optional
from datetime import datetime, timezone


class MonitoringService:
    def __init__(self):
        self.start_time = time.time()

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def get_cpu_percent(self) -> float:
        return psutil.cpu_percent(interval=0.1)

    def get_memory_info(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "percent": mem.percent,
            "used_mb": mem.used / (1024 * 1024),
            "total_mb": mem.total / (1024 * 1024),
        }

    def get_disk_info(self) -> float:
        disk = psutil.disk_usage("/")
        return disk.percent

    def get_system_status(self) -> dict:
        mem = self.get_memory_info()
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory_percent": mem["percent"],
            "memory_used_mb": round(mem["used_mb"], 2),
            "memory_total_mb": round(mem["total_mb"], 2),
            "disk_percent": self.get_disk_info(),
            "gpu": self.get_gpu_status(),
        }

    def get_gpu_status(self) -> dict:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, 0)
            pynvml.nvmlShutdown()
            return {
                "available": True,
                "name": name.decode() if isinstance(name, bytes) else name,
                "utilization": util.gpu,
                "memory_total_mb": round(mem_info.total / (1024 * 1024), 2),
                "memory_used_mb": round(mem_info.used / (1024 * 1024), 2),
                "temperature": temp,
            }
        except Exception:
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.total,memory.used,temperature.gpu", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(", ")
                    if len(parts) >= 5:
                        return {
                            "available": True,
                            "name": parts[0],
                            "utilization": float(parts[1].replace(" %", "")),
                            "memory_total_mb": float(parts[2].replace(" MiB", "").split(".")[0]),
                            "memory_used_mb": float(parts[3].replace(" MiB", "").split(".")[0]),
                            "temperature": float(parts[4]),
                        }
            except Exception:
                pass
            return {
                "available": False,
                "name": None,
                "utilization": None,
                "memory_total_mb": None,
                "memory_used_mb": None,
                "temperature": None,
            }
