import os, psutil

def system_snapshot() -> dict:
    process = psutil.Process(os.getpid())
    mem = process.memory_info()
    return {
        "process_cpu_percent": process.cpu_percent(interval=None),
        "process_rss_mb": round(mem.rss / 1024 / 1024, 2),
        "system_cpu_percent": psutil.cpu_percent(interval=None),
        "system_memory_percent": psutil.virtual_memory().percent,
    }
