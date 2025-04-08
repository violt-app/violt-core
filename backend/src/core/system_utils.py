"""
Violt Core Lite - System Utilities

This module provides system-specific utility functions for various platforms.
"""
import os
import sys
import platform
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


def get_system_info() -> Dict[str, str]:
    """Get system information in a platform-independent way."""
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "hostname": platform.node()
    }
    
    # Add platform-specific information
    if settings.IS_WINDOWS:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                info["windows_edition"] = winreg.QueryValueEx(key, "ProductName")[0]
                info["windows_build"] = winreg.QueryValueEx(key, "CurrentBuild")[0]
        except Exception as e:
            logger.warning(f"Failed to get Windows registry information: {e}")
    elif settings.IS_LINUX:
        try:
            # Try to get distribution information
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("PRETTY_NAME="):
                            info["linux_distribution"] = line.split("=")[1].strip().strip('"')
                            break
            
            # Check if running on Raspberry Pi
            if os.path.exists("/proc/device-tree/model"):
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read()
                    if "raspberry pi" in model.lower():
                        info["device_type"] = "Raspberry Pi"
                        info["device_model"] = model.strip('\0')
        except Exception as e:
            logger.warning(f"Failed to get Linux distribution information: {e}")
    
    return info


def restart_system() -> bool:
    """Restart the system in a platform-independent way."""
    logger.info(f"Attempting to restart system on platform {settings.PLATFORM}")
    
    try:
        if settings.IS_WINDOWS:
            # Windows restart
            subprocess.Popen(["shutdown", "/r", "/t", "5", "/c", "Violt Core Lite system restart"])
            return True
        elif settings.IS_LINUX:
            # Linux restart
            if os.geteuid() == 0:  # Running as root
                subprocess.Popen(["shutdown", "-r", "now"])
                return True
            else:
                # Try with sudo
                try:
                    subprocess.Popen(["sudo", "shutdown", "-r", "now"])
                    return True
                except Exception:
                    logger.warning("Failed to restart system: not running as root and sudo failed")
                    return False
        else:
            logger.warning(f"System restart not implemented for platform {settings.PLATFORM}")
            return False
    except Exception as e:
        logger.error(f"Failed to restart system: {e}")
        return False


def get_available_drives() -> List[str]:
    """Get available drives in a platform-independent way."""
    drives = []
    
    try:
        if settings.IS_WINDOWS:
            # Windows drives
            import string
            import ctypes
            
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:")
                bitmask >>= 1
        elif settings.IS_LINUX:
            # Linux mounts
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) > 1:
                        mount_point = parts[1]
                        if mount_point.startswith("/") and not mount_point.startswith("/proc") and not mount_point.startswith("/sys"):
                            drives.append(mount_point)
        
        return drives
    except Exception as e:
        logger.error(f"Failed to get available drives: {e}")
        return []


def get_disk_usage(path: str = None) -> Dict[str, float]:
    """Get disk usage information in a platform-independent way."""
    import psutil
    
    if path is None:
        # Use system drive if no path specified
        path = settings.SYSTEM_DRIVE
    
    try:
        usage = psutil.disk_usage(path)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent
        }
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {e}")
        return {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0
        }


def is_admin() -> bool:
    """Check if the current process has administrator/root privileges."""
    try:
        if settings.IS_WINDOWS:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix/Linux/Mac
            return os.geteuid() == 0
    except Exception:
        return False


def run_as_service() -> bool:
    """Check if the application is running as a service/daemon."""
    try:
        if settings.IS_WINDOWS:
            # Check if running as a Windows service
            import win32service
            import win32serviceutil
            import servicemanager
            return servicemanager.RunningAsService()
        else:
            # On Linux, check parent process
            import psutil
            parent = psutil.Process(os.getppid())
            return parent.name() in ["systemd", "init", "launchd"]
    except Exception:
        return False


def create_shortcut(target_path: str, shortcut_path: str, description: str = "") -> bool:
    """Create a shortcut/symlink in a platform-independent way."""
    try:
        target = Path(target_path)
        shortcut = Path(shortcut_path)
        
        if not target.exists():
            logger.error(f"Target path does not exist: {target_path}")
            return False
        
        if settings.IS_WINDOWS:
            # Windows shortcut
            import pythoncom
            from win32com.client import Dispatch
            
            shell = Dispatch("WScript.Shell")
            shortcut_file = shell.CreateShortCut(str(shortcut.with_suffix(".lnk")))
            shortcut_file.Targetpath = str(target)
            shortcut_file.Description = description
            shortcut_file.WorkingDirectory = str(target.parent)
            shortcut_file.save()
        else:
            # Unix symlink
            if shortcut.exists():
                os.remove(shortcut)
            os.symlink(target, shortcut)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create shortcut: {e}")
        return False
