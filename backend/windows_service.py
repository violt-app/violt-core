"""
Violt Core - Windows Service Wrapper

This module provides Windows service functionality for Violt Core.
It allows the application to run as a Windows service that can be started
automatically at system boot or manually by the user.
"""

import os
import sys
import time
import logging
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil
from pathlib import Path

# Add the parent directory to sys.path to allow importing the application
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))

# Import the application
from src.core.config import settings
from src.core.logger import setup_logging
from src.main import app
import uvicorn


class VioltService(win32serviceutil.ServiceFramework):
    """Windows Service class for Violt Core."""

    _svc_name_ = "VioltCore"
    _svc_display_name_ = "Violt Core Smart Home Automation"
    _svc_description_ = (
        "Local smart home automation platform for controlling devices and automations"
    )

    def __init__(self, args):
        """Initialize the service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False
        socket.setdefaulttimeout(60)

        # Set up logging
        self.log_file = (
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
            / "VioltCore"
            / "logs"
            / "service.log"
        )
        os.makedirs(self.log_file.parent, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename=str(self.log_file),
            filemode="a",
        )
        self.logger = logging.getLogger("VioltService")

    def SvcStop(self):
        """Stop the service."""
        self.logger.info("Stopping service...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        """Run the service."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self.logger.info("Starting service...")
        self.running = True
        self.main()

    def main(self):
        """Main service function."""
        try:
            self.logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

            # Create data directories
            data_dir = (
                Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
                / "VioltCore"
                / "data"
            )
            os.makedirs(data_dir, exist_ok=True)

            # Set environment variables for the application
            os.environ["VIOLT_DATA_DIR"] = str(data_dir)
            os.environ["VIOLT_CONFIG_DIR"] = str(data_dir / "config")
            os.environ["VIOLT_LOG_DIR"] = str(
                Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
                / "VioltCore"
                / "logs"
            )

            # Start the application in a separate thread
            import threading

            server_thread = threading.Thread(
                target=uvicorn.run,
                kwargs={
                    "app": "src.main:app",
                    "host": settings.HOST,
                    "port": settings.PORT,
                    "log_level": settings.LOG_LEVEL.lower(),
                },
            )
            server_thread.daemon = True
            server_thread.start()

            self.logger.info(
                f"Service started successfully on {settings.HOST}:{settings.PORT}"
            )

            # Wait for the stop event
            while self.running:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event received
                    break

            self.logger.info("Service stop event received")

        except Exception as e:
            self.logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(VioltService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(VioltService)
