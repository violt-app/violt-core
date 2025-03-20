# Violt Core Backlog (Open-Source)

## 1. Core Functionality

### Local Automation Engine (P1)

**Task:** Implement event-driven rule engine (triggers, conditions, actions).

**Definition of Done:** Users can create IFTTT-style rules for devices, with real-time event handling.

### Device Discovery & Setup (P1)

**Task:** Integrate autodiscovery for Zigbee, Z-Wave, Wi-Fi devices.

**Definition of Done:** Devices are automatically listed with basic info, and users can configure them.

### REST & WebSocket API (P1)

**Task:** Develop a documented API for controlling devices and managing automations.

**Definition of Done:** Swagger/OpenAPI docs with GET/POST endpoints for device interactions and rule creation.

### Basic UI Dashboard (P1)

**Task:** Provide a minimal web interface for device monitoring, rule setup, and system status.

**Definition of Done:** Users can toggle devices and create simple automations in a web app.

## 2. Security & Privacy

### Local Encryption & JWT Authentication (P2)

**Task:** Enforce TLS for local connections, add JWT tokens for session management.

**Definition of Done:** All local web/API calls are secured with TLS, and user sessions are validated.

### Role-Based Access Control (RBAC) (P3)

**Task:** Implement user roles (Admin, User, Guest) with restricted access to devices/automations.

**Definition of Done:** UI shows or hides features based on user roles.

### Logging & Auditing (P3)

**Task:** Maintain logs of user actions and device events. Provide a local audit trail.

**Definition of Done:** All device changes and rule modifications recorded with timestamps/user IDs.

## 3. Device Protocol Integrations

### MQTT Support (P2)

**Task:** Allow local MQTT broker for device messaging, handle topics for automation triggers.

**Definition of Done:** Users can publish/subscribe to topics, and device states are updated via MQTT.

### Matter & Thread Integration (P3)

**Task:** Implement Matter protocol stack for next-gen smart home devices.

**Definition of Done:** Basic Matter device pairing and control works in the local hub.

### Advanced Device Drivers (P3)

**Task:** Provide custom integrations for popular brands (Philips Hue, Nest, etc.).

**Definition of Done:** Users can easily add brand-specific devices with minimal configuration.

## 4. UI/UX Enhancements

### Responsive UI & Mobile Views (P2)

**Task:** Ensure the dashboard is mobile-friendly, with reactive layouts.

**Definition of Done:** On phones/tablets, the UI scales properly and is fully functional.

### Automation Templates & Wizard (P3)

**Task:** Offer pre-built automation templates (e.g., “If motion after 10 PM, turn on lights.”).

**Definition of Done:** Users can select from a library of templates to create rules.

### Visual Rule Builder (P3)

**Task:** Provide a drag-and-drop automation flow interface.

**Definition of Done:** Users can draw a workflow of triggers, conditions, and actions.

## 5. Community & Extensibility

### Plugin Architecture (P2)

**Task:** Allow third-party developers to add new integrations or custom scripts as plugins.

**Definition of Done:** Standard interface for installing/enabling/disabling plugins.

### Open-Source Documentation & Contributing Guide (P1)

**Task:** Provide developer docs for building integrations, raising PRs, etc.

**Definition of Done:** Detailed instructions in GitHub README and CONTRIBUTING.md.

### Localization & Multilingual Support (P4)

**Task:** Provide a framework for translations in the UI and logs.

**Definition of Done:** Users can switch language packs.
