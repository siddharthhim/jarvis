import asyncio
import logging
import psutil
from livekit.agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def get_system_info() -> str:
    """
    Returns a complete system health report: CPU, RAM, Disk, and Battery status.

    ONLY call this when the user explicitly asks about system status, 
    performance, health, or says something like 'what's up with the system',
    'system report', 'how is the system', 'system status'.
    Do NOT call this proactively or during normal conversations.
    """
    try:
        # CPU
        cpu_percent = await asyncio.to_thread(psutil.cpu_percent, 1)
        cpu_count = psutil.cpu_count(logical=True)

        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / (1024 ** 3), 1)
        ram_used_gb = round(ram.used / (1024 ** 3), 1)
        ram_percent = ram.percent

        # Disk (C drive)
        disk = psutil.disk_usage("C:\\")
        disk_total_gb = round(disk.total / (1024 ** 3), 1)
        disk_used_gb = round(disk.used / (1024 ** 3), 1)
        disk_percent = disk.percent

        # Battery
        battery = psutil.sensors_battery()
        if battery:
            batt_percent = round(battery.percent, 1)
            plugged = "Charging 🔌" if battery.power_plugged else "On Battery 🔋"
        else:
            batt_percent = "N/A"
            plugged = "No battery detected"

        report = (
            f"🖥️ System Report:\n"
            f"• CPU: {cpu_percent}% used ({cpu_count} logical cores)\n"
            f"• RAM: {ram_used_gb} GB / {ram_total_gb} GB used ({ram_percent}%)\n"
            f"• Disk (C:): {disk_used_gb} GB / {disk_total_gb} GB used ({disk_percent}%)\n"
            f"• Battery: {batt_percent}% — {plugged}"
        )

        logger.info("System info fetched.")
        return report

    except Exception as e:
        logger.exception(f"System info error: {e}")
        return f"❌ System info fetch करने में error आया: {e}"
