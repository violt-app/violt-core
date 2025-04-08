# Windows Installation Guide for Violt Core Lite

This guide provides step-by-step instructions for installing and running Violt Core Lite on Windows 10, Windows 11, and Windows Server.

## System Requirements

- Windows 10, Windows 11, or Windows Server 2016/2019/2022
- Python 3.11 or higher
- 2GB RAM minimum (4GB recommended)
- 1GB free disk space
- Administrator privileges for installation

## Installation Options

Violt Core Lite can be installed on Windows in two ways:

1. **Native Windows Installation**: Installs as a Windows service with automatic startup
2. **Docker-based Installation**: Runs in Docker containers (requires Docker Desktop for Windows)

## Option 1: Native Windows Installation

### Step 1: Install Python

1. Download Python 3.11 or higher from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Select "Install Now" for a standard installation or "Customize installation" for advanced options
4. Complete the installation

### Step 2: Download Violt Core Lite

1. Download the latest release from the official repository
2. Extract the ZIP file to a temporary location

### Step 3: Run the Windows Installer

1. Open Command Prompt as Administrator
2. Navigate to the extracted Violt Core Lite directory
3. Run the Windows installation script:

```
python windows_install.py
```

4. The installer will:
   - Check system requirements
   - Install required dependencies
   - Copy files to the installation directory (default: `C:\Program Files\VioltCoreLite`)
   - Create data directories (default: `C:\ProgramData\VioltCoreLite`)
   - Install and start the Windows service
   - Create shortcuts in the Start Menu

### Step 4: Access the Web Interface

1. Open a web browser
2. Navigate to [http://localhost:8000](http://localhost:8000)
3. Register a new user account
4. Start using Violt Core Lite!

### Installation Options

The Windows installer supports several command-line options:

```
python windows_install.py --help
```

Common options:
- `--install-dir PATH`: Specify a custom installation directory
- `--data-dir PATH`: Specify a custom data directory
- `--no-service`: Don't install as a Windows service
- `--no-shortcuts`: Don't create shortcuts

### Managing the Windows Service

The Violt Core Lite service can be managed using the Windows Service Manager or command line:

**Using Service Manager:**
1. Press Win+R, type `services.msc`, and press Enter
2. Find "Violt Core Lite Smart Home Automation" in the list
3. Right-click and select Start, Stop, or Restart

**Using Command Line:**
```
# Start the service
sc start VioltCoreLite

# Stop the service
sc stop VioltCoreLite

# Check service status
sc query VioltCoreLite
```

**Using Python Script:**
```
# Navigate to the installation directory
cd "C:\Program Files\VioltCoreLite\backend"

# Start the service
python windows_service.py start

# Stop the service
python windows_service.py stop

# Restart the service
python windows_service.py restart
```

### Service Configuration

The service startup type can be configured in the `.env` file located at `C:\ProgramData\VioltCoreLite\config\.env`:

```
# Set to "auto" for automatic startup or "manual" for manual startup
WINDOWS_SERVICE_STARTUP=auto
```

After changing this setting, restart the service for the changes to take effect.

## Option 2: Docker-based Installation

### Step 1: Install Docker Desktop for Windows

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Run the installer and follow the instructions
3. Start Docker Desktop and ensure it's running properly

### Step 2: Download Violt Core Lite

1. Download the latest release from the official repository
2. Extract the ZIP file to a location of your choice

### Step 3: Run with Docker Compose

1. Open Command Prompt or PowerShell
2. Navigate to the extracted Violt Core Lite directory
3. Run Docker Compose:

```
docker-compose up -d
```

4. This will:
   - Build the necessary Docker images
   - Create and start the containers
   - Set up the network between containers
   - Mount volumes for persistent data

### Step 4: Access the Web Interface

1. Open a web browser
2. Navigate to [http://localhost:3000](http://localhost:3000)
3. Register a new user account
4. Start using Violt Core Lite!

### Managing Docker Containers

```
# View running containers
docker-compose ps

# Stop containers
docker-compose stop

# Start containers
docker-compose start

# Restart containers
docker-compose restart

# Stop and remove containers
docker-compose down

# View logs
docker-compose logs -f
```

## Uninstalling Violt Core Lite

### Native Windows Installation

1. Open the Start Menu
2. Find "Violt Core Lite" folder
3. Click "Uninstall" or run the uninstaller from Control Panel
4. Follow the prompts to complete the uninstallation

Alternatively, run the uninstaller directly:
```
python "C:\Program Files\VioltCoreLite\uninstall.py"
```

### Docker-based Installation

1. Stop and remove containers:
```
docker-compose down
```

2. Optionally, remove volumes to delete all data:
```
docker-compose down -v
```

3. Delete the Violt Core Lite directory

## Troubleshooting

### Service Won't Start

1. Check the service logs at `C:\ProgramData\VioltCoreLite\logs\service.log`
2. Ensure Python is in the system PATH
3. Verify that all dependencies are installed correctly
4. Check Windows Event Viewer for system errors

### Can't Access Web Interface

1. Verify the service is running
2. Check if the port is already in use by another application
3. Ensure your firewall isn't blocking the connection
4. Try accessing with IP address instead of localhost: http://127.0.0.1:8000

### Permission Issues

1. Make sure you're running the installer as Administrator
2. Check that the service has appropriate permissions to access data directories
3. Verify that the user account running the service has sufficient privileges

## Getting Help

If you encounter issues not covered in this guide:

1. Check the full documentation in the `docs` directory
2. Look for similar issues in the project repository
3. Contact support with detailed information about your problem

## Next Steps

After installation, refer to the User Guide to learn how to:

1. Add and configure devices
2. Set up integrations with Xiaomi devices, Amazon Alexa, and Google Home
3. Create automation rules
4. Monitor your smart home system
