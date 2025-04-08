"""
Violt Core Lite - Windows Installation Script

This script installs Violt Core Lite as a Windows service and sets up the necessary
environment for running the application on Windows.
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
import winreg
import ctypes
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('violt_install.log')
    ]
)
logger = logging.getLogger('violt_installer')

# Default installation paths
DEFAULT_INSTALL_DIR = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "VioltCoreLite"
DEFAULT_DATA_DIR = Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / "VioltCoreLite"
DEFAULT_CONFIG_DIR = DEFAULT_DATA_DIR / "config"
DEFAULT_LOG_DIR = DEFAULT_DATA_DIR / "logs"
DEFAULT_DB_DIR = DEFAULT_DATA_DIR / "db"

# Required Python packages
REQUIRED_PACKAGES = [
    "fastapi>=0.95.0",
    "uvicorn>=0.21.1",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-jose>=3.3.0",
    "passlib>=1.7.4",
    "python-multipart>=0.0.6",
    "aiosqlite>=0.18.0",
    "psutil>=5.9.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "pywin32>=305",
    "websockets>=11.0.0",
    "pymongo>=4.3.0"
]


def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def check_python_version():
    """Check if Python version is compatible."""
    logger.info(f"Checking Python version: {sys.version}")
    major, minor, *_ = sys.version_info
    if major < 3 or (major == 3 and minor < 11):
        logger.error(f"Python 3.11+ is required, but found {major}.{minor}")
        return False
    return True


def install_dependencies():
    """Install required Python packages."""
    logger.info("Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        for package in REQUIRED_PACKAGES:
            logger.info(f"Installing {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def create_directories(install_dir, data_dir, config_dir, log_dir, db_dir):
    """Create necessary directories."""
    logger.info("Creating directories...")
    try:
        os.makedirs(install_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(db_dir, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False


def copy_files(source_dir, install_dir):
    """Copy application files to installation directory."""
    logger.info(f"Copying files from {source_dir} to {install_dir}...")
    try:
        # Copy backend files
        backend_source = source_dir / "backend"
        backend_dest = install_dir / "backend"
        
        if backend_source.exists():
            # Create backend directory if it doesn't exist
            os.makedirs(backend_dest, exist_ok=True)
            
            # Copy all files and subdirectories
            for item in backend_source.glob('**/*'):
                if item.is_file():
                    # Create parent directories if they don't exist
                    rel_path = item.relative_to(backend_source)
                    dest_path = backend_dest / rel_path
                    os.makedirs(dest_path.parent, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(item, dest_path)
        
        # Copy frontend files
        frontend_source = source_dir / "frontend"
        frontend_dest = install_dir / "frontend"
        
        if frontend_source.exists():
            # Create frontend directory if it doesn't exist
            os.makedirs(frontend_dest, exist_ok=True)
            
            # Copy all files and subdirectories
            for item in frontend_source.glob('**/*'):
                if item.is_file():
                    # Create parent directories if they don't exist
                    rel_path = item.relative_to(frontend_source)
                    dest_path = frontend_dest / rel_path
                    os.makedirs(dest_path.parent, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(item, dest_path)
        
        # Copy docs
        docs_source = source_dir / "docs"
        docs_dest = install_dir / "docs"
        
        if docs_source.exists():
            # Create docs directory if it doesn't exist
            os.makedirs(docs_dest, exist_ok=True)
            
            # Copy all files and subdirectories
            for item in docs_source.glob('**/*'):
                if item.is_file():
                    # Create parent directories if they don't exist
                    rel_path = item.relative_to(docs_source)
                    dest_path = docs_dest / rel_path
                    os.makedirs(dest_path.parent, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(item, dest_path)
        
        # Copy README and other root files
        for item in source_dir.glob('*.md'):
            shutil.copy2(item, install_dir)
        
        # Copy docker-compose.yml if it exists
        docker_compose = source_dir / "docker-compose.yml"
        if docker_compose.exists():
            shutil.copy2(docker_compose, install_dir)
        
        return True
    except Exception as e:
        logger.error(f"Failed to copy files: {e}")
        return False


def create_config_file(config_dir, data_dir, log_dir, db_dir):
    """Create configuration file."""
    logger.info("Creating configuration file...")
    try:
        config_file = config_dir / ".env"
        with open(config_file, "w") as f:
            f.write(f"# Violt Core Lite Configuration\n")
            f.write(f"APP_NAME=Violt Core Lite\n")
            f.write(f"APP_VERSION=1.0.0\n")
            f.write(f"DEBUG=false\n")
            f.write(f"HOST=0.0.0.0\n")
            f.write(f"PORT=8000\n")
            f.write(f"LOG_LEVEL=INFO\n")
            f.write(f"LOG_FILE={log_dir / 'violt.log'}\n")
            f.write(f"LOG_ROTATION=1 day\n")
            f.write(f"LOG_RETENTION=30 days\n")
            f.write(f"DATABASE_URL=sqlite:///{db_dir / 'violt.db'}\n")
            f.write(f"SECRET_KEY={os.urandom(24).hex()}\n")
            f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES=60\n")
            f.write(f"RELOAD=false\n")
            f.write(f"WORKERS=1\n")
            f.write(f"CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n")
            f.write(f"MONGODB_URL=mongodb://localhost:27017/violt\n")
            f.write(f"WINDOWS_SERVICE_STARTUP=auto\n")
        return True
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        return False


def install_windows_service(install_dir):
    """Install Windows service."""
    logger.info("Installing Windows service...")
    try:
        # Run the service installation command
        service_script = install_dir / "backend" / "windows_service.py"
        result = subprocess.run(
            [sys.executable, str(service_script), "install"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Service installation failed: {result.stderr}")
            return False
        
        logger.info("Service installed successfully")
        
        # Configure service to start automatically
        result = subprocess.run(
            [sys.executable, str(service_script), "start"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"Service start failed: {result.stderr}")
        else:
            logger.info("Service started successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to install Windows service: {e}")
        return False


def create_shortcuts(install_dir):
    """Create shortcuts in Start Menu."""
    logger.info("Creating shortcuts...")
    try:
        # Create Start Menu directory
        start_menu_dir = Path(os.environ.get('APPDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Violt Core Lite"
        os.makedirs(start_menu_dir, exist_ok=True)
        
        # Create shortcut for documentation
        import pythoncom
        from win32com.client import Dispatch
        
        shell = Dispatch("WScript.Shell")
        
        # Documentation shortcut
        docs_target = install_dir / "docs" / "README.md"
        if docs_target.exists():
            shortcut = shell.CreateShortCut(str(start_menu_dir / "Documentation.lnk"))
            shortcut.Targetpath = str(docs_target)
            shortcut.Description = "Violt Core Lite Documentation"
            shortcut.WorkingDirectory = str(docs_target.parent)
            shortcut.save()
        
        # Web UI shortcut
        shortcut = shell.CreateShortCut(str(start_menu_dir / "Web Interface.lnk"))
        shortcut.Targetpath = "http://localhost:8000"
        shortcut.Description = "Violt Core Lite Web Interface"
        shortcut.save()
        
        # Service Manager shortcut
        shortcut = shell.CreateShortCut(str(start_menu_dir / "Service Manager.lnk"))
        shortcut.Targetpath = "services.msc"
        shortcut.Description = "Windows Service Manager"
        shortcut.save()
        
        return True
    except Exception as e:
        logger.error(f"Failed to create shortcuts: {e}")
        return False


def add_to_registry(install_dir):
    """Add application information to Windows registry."""
    logger.info("Adding to Windows registry...")
    try:
        # Create registry key
        key_path = r"SOFTWARE\VioltCoreLite"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, 
                              subprocess.check_output("echo %date%", shell=True).decode().strip())
        
        # Create uninstaller entry
        uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\VioltCoreLite"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Violt Core Lite")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Violt")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, 
                              str(install_dir / "frontend" / "public" / "favicon.ico"))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 
                              f'"{sys.executable}" "{install_dir / "uninstall.py"}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        
        return True
    except Exception as e:
        logger.error(f"Failed to add to registry: {e}")
        return False


def create_uninstaller(install_dir, data_dir):
    """Create uninstaller script."""
    logger.info("Creating uninstaller...")
    try:
        uninstall_script = install_dir / "uninstall.py"
        with open(uninstall_script, "w") as f:
            f.write(f"""#!/usr/bin/env python
import os
import sys
import shutil
import subprocess
import ctypes
import winreg
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def main():
    if not is_admin():
        print("Administrator privileges required. Please run as administrator.")
        return False
    
    print("Uninstalling Violt Core Lite...")
    
    # Stop and remove service
    service_script = Path("{install_dir}") / "backend" / "windows_service.py"
    if service_script.exists():
        try:
            subprocess.run([sys.executable, str(service_script), "stop"], 
                          capture_output=True, text=True)
            subprocess.run([sys.executable, str(service_script), "remove"], 
                          capture_output=True, text=True)
            print("Service removed successfully")
        except Exception as e:
            print(f"Failed to remove service: {{e}}")
    
    # Remove Start Menu shortcuts
    start_menu_dir = Path(os.environ.get('APPDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Violt Core Lite"
    if start_menu_dir.exists():
        try:
            shutil.rmtree(start_menu_dir)
            print("Shortcuts removed successfully")
        except Exception as e:
            print(f"Failed to remove shortcuts: {{e}}")
    
    # Remove registry entries
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\VioltCoreLite")
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VioltCoreLite")
        print("Registry entries removed successfully")
    except Exception as e:
        print(f"Failed to remove registry entries: {{e}}")
    
    # Ask if user wants to keep data
    keep_data = input("Do you want to keep your data? (y/n): ").lower() == 'y'
    
    if not keep_data:
        data_dir = Path("{data_dir}")
        if data_dir.exists():
            try:
                shutil.rmtree(data_dir)
                print("Data removed successfully")
            except Exception as e:
                print(f"Failed to remove data: {{e}}")
    
    # Remove installation directory
    install_dir = Path("{install_dir}")
    
    # We need to remove the uninstaller script last, so we'll use a batch file
    batch_file = Path(os.environ.get('TEMP', '')) / "violt_uninstall.bat"
    with open(batch_file, "w") as f:
        f.write(f'''@echo off
echo Removing installation files...
timeout /t 2 > nul
rmdir /s /q "{{install_dir}}"
echo Violt Core Lite has been uninstalled.
echo.
pause
del "%~f0"
''')
    
    # Execute the batch file
    subprocess.Popen(["cmd", "/c", str(batch_file)])
    
    return True

if __name__ == "__main__":
    if not is_admin():
        # Re-run the script with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        main()
""")
        return True
    except Exception as e:
        logger.error(f"Failed to create uninstaller: {e}")
        return False


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install Violt Core Lite on Windows")
    parser.add_argument("--source", type=str, default=".", help="Source directory containing Violt Core Lite files")
    parser.add_argument("--install-dir", type=str, default=str(DEFAULT_INSTALL_DIR), help="Installation directory")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_DATA_DIR), help="Data directory")
    parser.add_argument("--no-service", action="store_true", help="Don't install as a Windows service")
    parser.add_argument("--no-shortcuts", action="store_true", help="Don't create shortcuts")
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    source_dir = Path(args.source).resolve()
    install_dir = Path(args.install_dir)
    data_dir = Path(args.data_dir)
    config_dir = data_dir / "config"
    log_dir = data_dir / "logs"
    db_dir = data_dir / "db"
    
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Installation directory: {install_dir}")
    logger.info(f"Data directory: {data_dir}")
    
    # Check if running as administrator
    if not is_admin():
        logger.error("Administrator privileges required. Please run as administrator.")
        return False
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create directories
    if not create_directories(install_dir, data_dir, config_dir, log_dir, db_dir):
        return False
    
    # Copy files
    if not copy_files(source_dir, install_dir):
        return False
    
    # Create configuration file
    if not create_config_file(config_dir, data_dir, log_dir, db_dir):
        return False
    
    # Install Windows service
    if not args.no_service:
        if not install_windows_service(install_dir):
            logger.warning("Failed to install Windows service, continuing with installation")
    
    # Create shortcuts
    if not args.no_shortcuts:
        if not create_shortcuts(install_dir):
            logger.warning("Failed to create shortcuts, continuing with installation")
    
    # Add to registry
    if not add_to_registry(install_dir):
        logger.warning("Failed to add to registry, continuing with installation")
    
    # Create uninstaller
    if not create_uninstaller(install_dir, data_dir):
        logger.warning("Failed to create uninstaller, continuing with installation")
    
    logger.info("Installation completed successfully!")
    logger.info(f"Violt Core Lite has been installed to {install_dir}")
    logger.info("You can access the web interface at http://localhost:8000")
    
    return True


if __name__ == "__main__":
    if not is_admin():
        # Re-run the script with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        success = main()
        if not success:
            logger.error("Installation failed!")
            sys.exit(1)
