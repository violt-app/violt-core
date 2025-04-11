[![Violt Core CI](https://github.com/violt-app/violt-core/actions/workflows/ci.yml/badge.svg)](https://github.com/violt-app/violt-core/actions/workflows/ci.yml)

# Violt Core Lite

Violt Core Lite is a local-only, open-source smart home automation platform designed to run on both Raspberry Pi and Windows systems. It provides a comprehensive solution for managing smart home devices, creating automation rules, and integrating with popular platforms like Xiaomi devices, Amazon Alexa, and Google Home.

## Features

- **Local-only execution** with no cloud dependency
- **Device management** for various smart home devices
- **Automation engine** with IF/THEN rules
- **Cross-platform support** for Raspberry Pi and Windows
- **Integration with popular platforms**:
  - Xiaomi devices
  - Amazon Alexa
  - Google Home
- **Real-time updates** via WebSockets
- **Responsive web interface** for desktop and mobile
- **Docker support** for easy deployment
- **Windows service** for native Windows installation

## System Requirements

### Raspberry Pi
- Raspberry Pi 3 or newer
- Raspberry Pi OS (32-bit or 64-bit)
- 2GB RAM minimum (4GB recommended)
- 1GB free disk space

### Windows
- Windows 10, Windows 11, or Windows Server 2016/2019/2022
- 2GB RAM minimum (4GB recommended)
- 1GB free disk space

## Installation Options

Violt Core Lite can be installed in several ways:

1. **Docker Installation** (cross-platform)
2. **Native Windows Installation**
3. **Native Raspberry Pi Installation**

### Docker Installation (Cross-Platform)

1. Install Docker and Docker Compose for your platform
2. Clone or download this repository
3. Navigate to the project directory
4. Run Docker Compose:

```bash
docker-compose up -d
```

5. Access the web interface at http://localhost:3000

For detailed Docker installation instructions, see [Docker Installation Guide](docs/docker_installation.md).

### Native Windows Installation

1. Install Python 3.11 or higher
2. Download or clone this repository
3. Run the Windows installer:

```
python windows_install.py
```

4. Access the web interface at http://localhost:8000

For detailed Windows installation instructions, see [Windows Installation Guide](docs/windows_installation.md).

### Native Raspberry Pi Installation

1. Install Python 3.11 or higher
2. Download or clone this repository
3. Run the installation script:

```bash
./install.sh
```

4. Access the web interface at http://localhost:8000

For detailed Raspberry Pi installation instructions, see [Raspberry Pi Installation Guide](docs/raspberry_pi_installation.md).

## Quick Start

After installation, follow these steps to get started:

1. Open the web interface in your browser
2. Register a new user account
3. Add your smart home devices
4. Create automation rules
5. Enjoy your automated smart home!

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Developer Guide](docs/developer_guide.md)
- [Windows Installation Guide](docs/windows_installation.md)
- [Raspberry Pi Installation Guide](docs/raspberry_pi_installation.md)
- [Docker Installation Guide](docs/docker_installation.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## Windows-Specific Features

When running on Windows, Violt Core Lite offers several platform-specific features:

- **Windows Service**: Runs as a background service that starts automatically with Windows
- **Command-Line Interface**: Manage the application using the `violt.bat` script
- **Start Menu Integration**: Easy access to the web interface and documentation
- **Registry Integration**: Proper Windows application registration

To manage Violt Core Lite on Windows, use the provided batch script:

```
violt.bat install   # Install the application
violt.bat start     # Start the service
violt.bat stop      # Stop the service
violt.bat restart   # Restart the service
violt.bat status    # Check service status
violt.bat uninstall # Uninstall the application
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Home Assistant](https://github.com/home-assistant/core) for inspiration and reference
- All the open-source libraries and frameworks that made this project possible
