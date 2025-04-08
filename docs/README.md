# Violt Core Lite Documentation

## Overview

Violt Core Lite is an open-source, local-only smart home automation platform designed to run on a Raspberry Pi or local server. It provides a complete solution for managing smart home devices, creating automation rules, and integrating with popular platforms like Xiaomi devices, Amazon Alexa, and Google Home.

This documentation covers the architecture, installation, configuration, and usage of Violt Core Lite.

## Table of Contents

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [API Reference](#api-reference)
5. [Frontend Interface](#frontend-interface)
6. [Device Integration](#device-integration)
7. [Automation Rules](#automation-rules)
8. [Security](#security)
9. [Contributing](#contributing)
10. [License](#license)

## Architecture

Violt Core Lite follows a modular architecture with clear separation of concerns:

### Backend

- **Core**: Configuration, startup, authentication, and logging
- **Database**: SQLite database with SQLAlchemy ORM
- **API**: FastAPI endpoints for devices, automations, and system management
- **Devices**: Modular device integration framework
- **Automation**: Rule engine for triggers, conditions, and actions
- **WebSockets**: Real-time communication for UI updates

### Frontend

- **Next.js**: React framework with App Router
- **ShadCN UI**: Component library built on TailwindCSS and Radix
- **Context Providers**: State management for authentication, devices, and automations
- **Pages**: Dashboard, device management, automation rules, and settings

### System Integration

- **REST API**: Local-only API secured with JWT tokens
- **WebSockets**: Real-time updates for device states and events
- **Local Storage**: Persistent state using SQLite
- **Docker**: Containerized deployment for easy installation

## Installation

### Prerequisites

- Docker and Docker Compose
- Raspberry Pi 4 (or equivalent) with 2GB+ RAM
- Network access to your smart home devices

### Using Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/violt/violt-core-lite.git
   cd violt-core-lite
   ```

2. Create environment files:
   ```bash
   cp backend/config/.env.example backend/config/.env
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the web interface at `http://your-raspberry-pi-ip:8000`

### Manual Installation

#### Backend

1. Install Python 3.11+:
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp config/.env.example config/.env
   # Edit .env file with your settings
   ```

5. Run the application:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

#### Frontend

1. Install Node.js 20+:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Build the application:
   ```bash
   npm run build
   ```

4. Start the frontend:
   ```bash
   npm start
   ```

## Configuration

### Backend Configuration

The backend is configured through environment variables in the `.env` file:

```
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=sqlite:///./violt.db

# MongoDB Analytics (optional)
MONGODB_URI=mongodb://username:password@host:port/database
MONGODB_ENABLED=false

# Device Discovery
DEVICE_DISCOVERY_INTERVAL=300  # seconds
```

### Device Integration Configuration

Device integrations are configured through YAML files in the `config/integrations` directory:

```yaml
# config/integrations/xiaomi.yaml
enabled: true
discovery:
  enabled: true
  interval: 300  # seconds
```

### Automation Engine Configuration

The automation engine is configured through environment variables:

```
AUTOMATION_CHECK_INTERVAL=10  # seconds
AUTOMATION_MAX_HISTORY=100    # events
```

## API Reference

Violt Core Lite provides a comprehensive REST API for managing devices, automations, and system settings.

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register a new user |
| `/api/auth/login` | POST | Login and get access token |
| `/api/auth/me` | GET | Get current user information |

### Devices

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices` | GET | List all devices |
| `/api/devices` | POST | Add a new device |
| `/api/devices/{id}` | GET | Get device details |
| `/api/devices/{id}` | PUT | Update device |
| `/api/devices/{id}` | DELETE | Remove device |
| `/api/devices/{id}/command` | POST | Execute device command |

### Automations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/automations` | GET | List all automations |
| `/api/automations` | POST | Create a new automation |
| `/api/automations/{id}` | GET | Get automation details |
| `/api/automations/{id}` | PUT | Update automation |
| `/api/automations/{id}` | DELETE | Remove automation |
| `/api/automations/{id}/toggle` | POST | Enable/disable automation |
| `/api/automations/{id}/duplicate` | POST | Duplicate automation |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/status` | GET | Get system status |
| `/api/system/logs` | GET | Get system logs |
| `/api/system/restart` | POST | Restart the system |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/api/ws` | WebSocket connection for real-time updates |

## Frontend Interface

The frontend provides a user-friendly interface for managing your smart home:

### Pages

- **Dashboard**: Overview of devices, automations, and system status
- **Devices**: Add, edit, and control smart home devices
- **Automations**: Create and manage automation rules
- **Settings**: Configure system settings and integrations

### Authentication

- User registration with terms acceptance
- Login with JWT token authentication
- Automatic token refresh

### Device Management

- Add devices manually or through discovery
- Group devices by room or type
- Control device states (on/off, brightness, color, etc.)
- View device history and statistics

### Automation Rules

- Create IF/THEN rules with multiple triggers and actions
- Schedule-based automations (time, sunrise/sunset)
- Device state-based automations
- Condition-based logic (AND/OR)

## Device Integration

Violt Core Lite supports multiple device integration platforms:

### Xiaomi Devices

- Yeelight smart bulbs
- Mi Home sensors and switches
- Xiaomi vacuum cleaners
- Other Mi Home ecosystem devices

### Amazon Alexa

- Voice control through Alexa Skills
- Device discovery and control
- State synchronization

### Google Home

- Voice control through Google Assistant
- Device discovery and control
- State synchronization

### Adding New Integrations

Violt Core Lite follows a modular approach for device integrations. To add a new integration:

1. Create a new module in `backend/src/devices/{integration_name}/`
2. Implement the required interfaces from `backend/src/devices/base.py`
3. Register the integration in `backend/src/devices/registry.py`
4. Add configuration in `config/integrations/{integration_name}.yaml`

## Automation Rules

The automation engine allows creating powerful rules to automate your smart home:

### Triggers

- **Time**: Specific time or recurring schedule
- **Sun**: Sunrise, sunset with offset
- **Device State**: When a device changes state
- **Event**: System events (startup, device added, etc.)

### Conditions

- **Time**: Time range or day of week
- **Sun**: Before/after sunrise/sunset
- **Device State**: Current state of a device
- **Numeric**: Value comparison (greater than, less than, etc.)
- **Boolean**: AND/OR/NOT operations

### Actions

- **Device Command**: Control a device
- **Delay**: Wait before next action
- **Notification**: Send a notification
- **Scene**: Activate multiple devices
- **Webhook**: Call an external API
- **Conditional**: IF/THEN/ELSE logic

## Security

Violt Core Lite implements several security measures:

- **Local-only**: No cloud dependency or external connections
- **JWT Authentication**: Secure token-based authentication
- **HTTPS Support**: Optional TLS encryption
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error responses

## Contributing

We welcome contributions to Violt Core Lite! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

1. Clone the repository
2. Install development dependencies
3. Run tests with pytest
4. Follow the coding standards (PEP 8 for Python, ESLint for JavaScript)

## License

Violt Core Lite is released under the MIT License. See the LICENSE file for details.
