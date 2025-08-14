# WinAgent MCP

A Model Context Protocol (MCP) server that enables Claude AI to perform Windows system administration and monitoring tasks. Built with FastMCP and designed for local Claude Desktop integration.

### System Information Tool
- **get_system_info**: Comprehensive Windows system information including:
  - OS version and hardware details
  - CPU specifications and real-time usage
  - Memory (RAM) statistics in GB
  - Disk drive information and storage usage
  - Network configuration (hostname, local IP)
  - System boot time and uptime

### Process Management Tool
- **get_top_resource_processes**: Intelligent process monitoring that identifies:
  - Top processes consuming the most system resources
  - Combined CPU + Memory resource scoring (60% CPU, 40% Memory weighting)
  - Memory usage in MB for easy understanding
  - Process age and command line information
  - Summary statistics of total resource consumption

## Features

- **Safety First**: Built-in security checks prevent access to protected system directories
- **Comprehensive Error Handling**: Follows project coding standards with proper exception handling
- **Real-time Data**: Live system metrics and process information
- **Resource Intelligence**: Ranking of processes by actual resource impact

## Quick Start

1. **Install dependencies**:
   ```bash
   uv add fastmcp psutil
   ```

2. **Run the MCP server**:
   ```bash
   uv run python server.py
   ```

3. **Connect to Claude Desktop**: The server is configured to work with Claude Desktop via MCP protocol

## Current Tools

| Tool Name | Description | Output |
|-----------|-------------|---------|
| `get_system_info` | Complete system overview | Hardware specs, OS info, resource usage |
| `get_top_resource_processes` | Resource-consuming processes | Top 10 processes by CPU+Memory usage |

## Technical Details

- **Framework**: FastMCP for Model Context Protocol
- **Language**: Python 3.12+
- **Dependencies**: psutil for system monitoring, FastMCP for MCP integration
- **Platform**: Windows 10/11 optimized
- **Environment**: UV package manager for dependency management

