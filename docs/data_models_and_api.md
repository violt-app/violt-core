# Data Models and API Endpoints for Violt Core Lite

## Core Data Models

### User
- `id`: Unique identifier (UUID)
- `username`: Username for login
- `email`: Email address
- `password_hash`: Hashed password
- `created_at`: Timestamp of account creation
- `last_login`: Timestamp of last login
- `settings`: JSON field for user preferences
- `terms_accepted`: Boolean indicating acceptance of terms

### Device
- `id`: Unique identifier (UUID)
- `name`: User-friendly name
- `type`: Device type (e.g., "light", "switch", "sensor")
- `manufacturer`: Device manufacturer (e.g., "Xiaomi", "Generic")
- `model`: Device model number/name
- `location`: Room or area where device is located
- `ip_address`: IP address (for network devices)
- `mac_address`: MAC address (for network devices)
- `status`: Current device status (online/offline)
- `properties`: JSON field for device-specific properties
- `state`: JSON field for current device state
- `created_at`: Timestamp of device addition
- `last_updated`: Timestamp of last state update
- `integration_type`: Integration method (e.g., "xiaomi", "alexa", "google_home")
- `config`: JSON field for device configuration

### Automation
- `id`: Unique identifier (UUID)
- `name`: User-friendly name
- `description`: Description of automation purpose
- `enabled`: Boolean indicating if automation is active
- `trigger_type`: Type of trigger (e.g., "device", "time", "condition")
- `trigger_config`: JSON field for trigger configuration
- `condition_type`: Type of condition (e.g., "and", "or", "none")
- `conditions`: JSON array of condition objects
- `action_type`: Type of action (e.g., "device", "notification")
- `actions`: JSON array of action objects
- `created_at`: Timestamp of automation creation
- `last_triggered`: Timestamp of last trigger
- `execution_count`: Count of successful executions
- `last_modified`: Timestamp of last modification

### Event
- `id`: Unique identifier (UUID)
- `type`: Event type (e.g., "device_state_change", "automation_triggered")
- `source`: Source of the event (device ID, system, etc.)
- `data`: JSON field for event data
- `timestamp`: When the event occurred
- `processed`: Boolean indicating if event was processed by automation engine

### Log
- `id`: Unique identifier (UUID)
- `level`: Log level (info, warning, error, debug)
- `source`: Source of the log (component name)
- `message`: Log message
- `data`: JSON field for additional data
- `timestamp`: When the log was created

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login and get access token
- `POST /api/auth/logout`: Logout and invalidate token
- `GET /api/auth/me`: Get current user information
- `PUT /api/auth/me`: Update user information
- `POST /api/auth/terms`: Accept terms and conditions

### Devices
- `GET /api/devices`: List all devices
- `GET /api/devices/{id}`: Get device details
- `POST /api/devices`: Add a new device
- `PUT /api/devices/{id}`: Update device information
- `DELETE /api/devices/{id}`: Remove a device
- `GET /api/devices/{id}/state`: Get current device state
- `PUT /api/devices/{id}/state`: Update device state (control device)
- `POST /api/devices/discover`: Discover new devices on network
- `GET /api/devices/types`: Get list of supported device types
- `GET /api/devices/manufacturers`: Get list of supported manufacturers

### Automations
- `GET /api/automations`: List all automations
- `GET /api/automations/{id}`: Get automation details
- `POST /api/automations`: Create a new automation
- `PUT /api/automations/{id}`: Update automation
- `DELETE /api/automations/{id}`: Remove an automation
- `PUT /api/automations/{id}/enable`: Enable automation
- `PUT /api/automations/{id}/disable`: Disable automation
- `GET /api/automations/{id}/history`: Get automation execution history
- `POST /api/automations/{id}/test`: Test automation without executing actions

### System
- `GET /api/system/status`: Get system status
- `GET /api/system/stats`: Get system statistics
- `POST /api/system/restart`: Restart the system
- `GET /api/system/logs`: Get system logs
- `POST /api/system/backup`: Create system backup
- `POST /api/system/restore`: Restore from backup
- `GET /api/system/updates`: Check for updates

### Integrations
- `GET /api/integrations`: List all available integrations
- `GET /api/integrations/{type}`: Get integration details
- `POST /api/integrations/{type}/setup`: Setup integration
- `DELETE /api/integrations/{type}`: Remove integration
- `GET /api/integrations/{type}/devices`: List devices for integration
- `POST /api/integrations/{type}/sync`: Sync devices with integration

### Events
- `GET /api/events`: Get recent events
- `GET /api/events/{id}`: Get event details
- `GET /api/events/device/{device_id}`: Get events for specific device

## WebSocket Endpoints

- `/ws/devices`: Real-time device state updates
- `/ws/automations`: Real-time automation status updates
- `/ws/events`: Real-time system events

## Integration Specifications

### Xiaomi Integration
- Protocol: Xiaomi MIoT Protocol
- Discovery: mDNS/Bonjour
- Authentication: Token-based
- Supported Devices: Lights, switches, sensors, vacuums
- Configuration: IP address, token

### Amazon Alexa Integration
- Protocol: Smart Home Skill API
- Authentication: OAuth 2.0
- Capabilities: Device discovery, state reporting, voice commands
- Configuration: Skill ID, client ID, client secret

### Google Home Integration
- Protocol: Smart Home Actions API
- Authentication: OAuth 2.0
- Capabilities: Device discovery, state reporting, voice commands
- Configuration: Project ID, client ID, client secret

## MongoDB Integration
- Purpose: Store usage data and user information
- Data Collected:
  - Anonymous usage statistics
  - Device types and counts
  - Automation patterns
  - System performance metrics
  - User registration data (with consent)
- Configuration: Connection string, database name, collection names
