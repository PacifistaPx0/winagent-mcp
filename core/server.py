import asyncio
import json
import os
import tempfile
import platform
import socket
import psutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel

# Initialize the MCP server
mcp = FastMCP("WinAgent MCP")

# Security configuration
PROTECTED_PATHS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData\\Microsoft\\Windows",
    "C:\\System Volume Information"
]

class Settings:
    """Configuration management for WinAgent MCP."""
    ENABLE_DESTRUCTIVE_OPERATIONS: bool = False
    REQUIRE_CONFIRMATION: bool = True
    MAX_FILE_SIZE_MB: int = 100
    LOG_LEVEL: str = "INFO"
    PROCESS_TIMEOUT: int = 30
    SERVICE_TIMEOUT: int = 60
    TEMP_DIR: str = tempfile.gettempdir()
    BACKUP_DIR: str = os.path.join(os.getenv('USERPROFILE', ''), 'WinAgent_Backups')

def validate_path(path: str) -> bool:
    """Validate that a path is safe to access."""
    try:
        resolved_path = Path(path).resolve()
        path_str = str(resolved_path)
        
        # Check against protected paths
        for protected in PROTECTED_PATHS:
            if path_str.startswith(protected):
                return False
        return True
    except Exception:
        return False

@mcp.tool(
    name="get_system_info",
    description="Get comprehensive Windows system information including hardware and OS details"
)
def get_system_info() -> List[Dict[str, Any]]:
    """
    Get comprehensive Windows system information including hardware and OS details.
    
    Provides detailed information about:
    - Operating system version and details
    - CPU specifications and current usage
    - Memory (RAM) statistics
    - Disk drives and storage information
    - Network configuration
    - System uptime and boot time
    
    Returns:
        List containing system information dictionary with success status
    """
    try:
        print("DEBUG: Starting system information gathering...")
        
        # Get basic system information
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": socket.gethostname(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        }
        
        # Get CPU information
        cpu_freq = psutil.cpu_freq()
        system_info["cpu"] = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_frequency_mhz": round(cpu_freq.current) if cpu_freq else "Unknown",
            "max_frequency_mhz": round(cpu_freq.max) if cpu_freq else "Unknown",
            "cpu_usage_percent": psutil.cpu_percent(interval=1)
        }
        
        # Get memory information
        memory = psutil.virtual_memory()
        system_info["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": memory.percent
        }
        
        # Get disk information
        system_info["disks"] = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "usage_percent": round((usage.used / usage.total) * 100, 1)
                }
                system_info["disks"].append(disk_info)
            except PermissionError:
                # Skip inaccessible drives
                continue
        
        # Get network information
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            system_info["network"] = {
                "hostname": hostname,
                "local_ip": local_ip
            }
        except Exception:
            system_info["network"] = {
                "hostname": "Unknown",
                "local_ip": "Unknown"
            }
        
        print("DEBUG: System information gathered successfully")
        
        return [{
            "success": True,
            "data": system_info,
            "message": "System information retrieved successfully"
        }]
        
    except PermissionError as e:
        error_msg = f"Permission denied accessing system information: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        return [{
            "success": False,
            "error": error_msg
        }]
    except Exception as e:
        error_msg = f"Failed to get system information: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        return [{
            "success": False,
            "error": error_msg
        }]

@mcp.tool(
    name="get_top_resource_processes", 
    description="Get the top processes consuming the most system resources (CPU + Memory combined)"
)
def get_top_resource_processes(limit: Optional[int] = 10) -> List[Dict[str, Any]]:
    """
    Get the top processes consuming the most system resources.
    
    Combines CPU and memory usage to identify the most resource-intensive processes.
    Also includes additional process details like memory usage in MB, command line, etc.
    
    Args:
        limit: Maximum number of processes to return (default: 10, max: 50)
        
    Returns:
        List containing top resource-consuming processes with success status
    """
    try:
        # Validate and set limit
        if limit is None or limit <= 0:
            limit = 10
        elif limit > 50:
            limit = 50
            
        print(f"DEBUG: Getting top {limit} resource-consuming processes...")
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'cmdline']):
            try:
                proc_info = proc.info
                cpu_percent = proc_info['cpu_percent'] or 0
                memory_percent = proc_info['memory_percent'] or 0
                
                # Calculate combined resource score (weighted: 60% CPU, 40% Memory)
                resource_score = (cpu_percent * 0.6) + (memory_percent * 0.4)
                
                # Get memory usage in MB
                memory_mb = 0
                if proc_info['memory_info']:
                    memory_mb = round(proc_info['memory_info'].rss / (1024 * 1024), 2)
                
                # Get process command line (first 100 chars to avoid too long output)
                cmdline = ""
                if proc_info['cmdline']:
                    cmdline = " ".join(proc_info['cmdline'])[:100]
                
                # Get process age
                process_age = ""
                if proc_info['create_time']:
                    age_seconds = datetime.now().timestamp() - proc_info['create_time']
                    if age_seconds < 60:
                        process_age = f"{int(age_seconds)}s"
                    elif age_seconds < 3600:
                        process_age = f"{int(age_seconds/60)}m"
                    else:
                        process_age = f"{int(age_seconds/3600)}h"
                
                processes.append({
                    "pid": proc_info['pid'],
                    "name": proc_info['name'],
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory_percent, 2),
                    "memory_mb": memory_mb,
                    "resource_score": round(resource_score, 2),
                    "status": proc_info['status'],
                    "age": process_age,
                    "cmdline": cmdline
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes we can't access
                continue
        
        # Sort by combined resource score (highest first)
        processes.sort(key=lambda x: x['resource_score'], reverse=True)
        processes = processes[:limit]
        
        # Calculate total system resource usage from top processes
        total_cpu = sum(proc['cpu_percent'] for proc in processes)
        total_memory_mb = sum(proc['memory_mb'] for proc in processes)
        
        print(f"DEBUG: Retrieved {len(processes)} top resource-consuming processes")
        
        return [{
            "success": True,
            "data": {
                "top_processes": processes,
                "summary": {
                    "total_processes_shown": len(processes),
                    "limit_applied": limit,
                    "combined_cpu_usage": round(total_cpu, 2),
                    "combined_memory_mb": round(total_memory_mb, 2),
                    "combined_memory_gb": round(total_memory_mb / 1024, 2)
                }
            },
            "message": f"Retrieved top {len(processes)} resource-consuming processes"
        }]
        
    except Exception as e:
        error_msg = f"Failed to get top resource processes: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        return [{
            "success": False,
            "error": error_msg
        }]

def main():
    """Main entry point for the MCP server."""
    print("Starting WinAgent MCP Server with System Information tools")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()

