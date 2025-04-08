# Violt Core Lite - Project Architecture

## Overview

Violt Core Lite is a local-only, open-source smart home automation platform designed to run on Raspberry Pi or local servers. It provides a complete solution for managing smart home devices, creating automations, and integrating with popular platforms like Xiaomi devices, Amazon Alexa, and Google Home.

## System Architecture

The system follows a modular architecture with clear separation of concerns:

```
violt-core-lite/
├── backend/                  # Python FastAPI backend
│   ├── src/
│   │   ├── api/              # API endpoints and routers
│   │   ├── automation/       # Automation engine and rules
│   │   ├── core/             # Core system functionality
│   │   ├── database/         # Database models and connections
│   │   ├── devices/          # Device integration modules
│   │   ├── utils/            # Utility functions and helpers
│   │   └── tests/            # Backend unit tests
│   ├── config/               # Configuration files
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js frontend
│   ├── app/                  # App Router pages
│   ├── components/           # React components
│   ├── lib/                  # Frontend utilities
│   ├── public/               # Static assets
│   ├── styles/               # CSS and styling
│   └── tests/                # Frontend tests
├── docs/                     # Documentation
│   ├── backend/              # Backend documentation
│   ├── frontend/             # Frontend documentation
│   ├── deployment/           # Deployment guides
│   └── contribution/         # Contribution guidelines
└── docker/                   # Docker configuration
    ├── Dockerfile            # Main Dockerfile
    └── docker-compose.yml    # Docker Compose configuration
```

## Backend Architecture

The backend follows a layered architecture:

1. **API Layer**: FastAPI endpoints that handle HTTP requests and responses
2. **Service Layer**: Business logic and core functionality
3. **Data Access Layer**: Database interactions via SQLAlchemy
4. **Integration Layer**: Modules for third-party device integration

### Key Components:

- **Device Management**: CRUD operations for managing smart devices
- **Automation Engine**: Rule-based system for creating and executing automations
- **WebSocket Server**: Real-time communication with frontend
- **Background Worker**: Scheduled tasks for automation triggers
- **Database**: SQLite for persistent storage
- **Analytics**: MongoDB integration for usage data

## Frontend Architecture

The frontend follows the Next.js App Router architecture:

1. **Pages**: Route-based React components
2. **Components**: Reusable UI elements using ShadCN
3. **State Management**: Local state with context or Zustand
4. **API Client**: Communication with backend services

### Key Features:

- **Dashboard**: Overview of all devices and automations
- **Device Control**: UI for controlling smart devices
- **Automation Builder**: IFTTT-style interface for creating automations
- **User Registration**: Initial setup and terms acceptance
- **Responsive Design**: Mobile and desktop compatibility

## Data Flow

1. User interacts with frontend UI
2. Frontend sends requests to backend API
3. Backend processes requests and interacts with devices
4. Device state changes are communicated back to frontend via WebSockets
5. Automation engine monitors conditions and triggers actions
6. Usage data is sent to MongoDB for analytics

## Integration Points

- **Xiaomi Devices**: Direct integration via local network
- **Amazon Alexa**: Voice control integration
- **Google Home**: Voice control integration
- **MongoDB**: External database for usage analytics

## Security

- Local-only execution with no cloud dependency
- API secured with token or header authentication
- User consent required for data collection

## Deployment

- Docker containers for easy deployment
- Optimized for Raspberry Pi and local servers
- Persistent storage for configurations and state

## Extensibility

The system follows a drop-in modular framework to easily add new device configurations with minimal effort. Configuration files use YAML or JSON format for simplicity and readability.
