# Novamind-Backend WSL2 Migration

## Overview

The Novamind-Backend platform has been migrated to use WSL2 (Windows Subsystem for Linux) with Ubuntu 22.04 as the standardized development and testing environment. This document outlines the migration process and how to set up your environment.

## Why WSL2?

WSL2 provides a consistent Linux environment that combines the best of both worlds:

1. **Consistency**: All developers work with the same Ubuntu 22.04 environment, eliminating "it works on my machine" problems
2. **HIPAA Compliance**: Security testing tools run natively in Linux for more accurate results
3. **Performance**: WSL2 offers near-native Linux performance while still using Windows as your primary OS
4. **Compatibility**: Seamless integration with Windows filesystem and tools like VSCode

## Setup Instructions

### Quick Start

For most users, the simplest setup is to run:

```
scripts\setup_wsl2_environment.bat
```

This will:
1. Check if WSL2 with Ubuntu 22.04 is installed
2. Run the unified WSL2 setup script
3. Configure proper symlinks and permissions

### Manual Setup

If you prefer to set up manually:

1. **Install WSL2 with Ubuntu 22.04**:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

2. **Run the setup script from WSL2**:
   ```bash
   cd /path/to/Novamind-Backend
   ./scripts/unified_wsl2_setup.sh
   ```

## Running HIPAA Security Tests

### From Windows

```
scripts\run_hipaa_security.bat
```

or 

```powershell
.\scripts\Run-HIPAASecurityTests.ps1
```

### From WSL2

```bash
./scripts/run_hipaa_security.sh
```

## Project Structure

The HIPAA security testing infrastructure uses the following architecture:

```
📁 scripts/
├── 📄 run_hipaa_security.bat        # Windows batch entry point
├── 📄 Run-HIPAASecurityTests.ps1    # PowerShell entry point
├── 📄 run_hipaa_security.sh         # WSL2 shell script entry point
├── 📄 run_hipaa_security_suite.py   # Core Python test logic
├── 📄 setup_wsl2_environment.bat    # Windows WSL2 setup entry point
├── 📄 unified_wsl2_setup.sh         # WSL2 environment setup script
└── 📄 wsl2_migration_guide.md       # Detailed migration guide

📁 security-reports/                 # Generated security reports
```

## Virtual Environment

All WSL2 scripts now use a consistent virtual environment at `./venv`. The environment includes:

- Core project dependencies from `requirements.txt`
- Security testing tools from `requirements-security.txt`
- Development tools from `requirements-dev.txt`

## Windows-WSL2 Integration

The setup scripts automatically create symlinks between Windows and WSL2 paths:

```
/mnt/c/Users/USERNAME/Desktop/NOVAMIND-WEB/Novamind-Backend ➡️ /home/USERNAME/novamind-backend
```

This ensures:
1. Files created/edited in WSL2 are visible in Windows
2. Files created/edited in Windows are visible in WSL2
3. Tools like VSCode can seamlessly access files from both environments

## Development Workflow

1. **Code in Windows**: Use your preferred Windows IDE (VSCode recommended)
2. **Run/Test in WSL2**: Execute tests in the Linux environment for accurate results
3. **Security Testing**: Run HIPAA compliance checks using the provided scripts

## Troubleshooting

### Permission Issues

If you encounter permission errors in WSL2:

```bash
sudo chmod -R 755 /path/to/Novamind-Backend
```

### WSL2 Not Found

If Windows cannot find WSL2:

```powershell
wsl --install
```

Then restart your computer.

### Python Version Issues

The security scripts require Python 3.7+. To check your Python version:

```bash
python3 --version
```

To install a newer Python version in Ubuntu:

```bash
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

## Further Documentation

- [Detailed Migration Guide](../scripts/wsl2_migration_guide.md)
- [WSL2 Microsoft Documentation](https://docs.microsoft.com/en-us/windows/wsl/install)
- [VSCode WSL Development](https://code.visualstudio.com/docs/remote/wsl)