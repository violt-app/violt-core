# Violt Core Lite - Technical Requirements and Implementation Plan

## Backend Requirements

### Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT token-based authentication
- **Real-time**: WebSockets for live updates
- **Background Tasks**: Background worker for automation triggers

### Modular Architecture
- `/src/api`: API endpoints and routers
- `/src/devices`: Device integration modules
- `/src/automation`: Automation engine and rule processing
- `/src/core`: Core system functionality
- `/src/database`: Database models and connections
- `/src/utils`: Utility functions and helpers
- `/src/tests`: Unit and integration tests

### Device Integration
- Modular plugin system for device types
- YAML/JSON configuration files for device specifications
- Support for Xiaomi devices via MIoT protocol
- Amazon Alexa integration via Smart Home Skill API
- Google Home integration via Smart Home Actions API

### Automation Engine
- Rule-based system with IF/THEN logic
- Support for time-based, device-state, and condition triggers
- Background worker to evaluate rules every 5-10 seconds
- Event-driven architecture for real-time responses

### Data Storage
- SQLite for persistent local storage
- SQLAlchemy for ORM and database operations
- MongoDB integration for optional usage analytics

### Testing and Documentation
- Pytest for unit and integration tests
- 80%+ test coverage
- OpenAPI auto-generated documentation
- Comprehensive developer documentation

## Frontend Requirements

### Core Technologies
- **Framework**: Next.js with App Router
- **UI Library**: ShadCN (TailwindCSS + Radix + React 19)
- **State Management**: Local state with context or Zustand
- **API Client**: Fetch or Axios for API communication
- **Real-time**: WebSocket client for live updates

### Key Features
- Responsive dashboard with device overview
- Device control interface with toggles and sliders
- Automation builder with IFTTT-style interface
- User registration and terms acceptance
- Mobile-friendly design

### Component Structure
- Layout components for consistent UI
- Reusable UI components for devices and automations
- Form components for data entry
- Modal components for confirmations and alerts
- Dashboard widgets for system status

### State Management
- Device state management
- Automation state management
- User preferences and settings
- Real-time updates via WebSockets

## Deployment Requirements

### Docker Configuration
- Multi-stage build for optimized images
- Docker Compose for service orchestration
- Volume mounts for persistent data
- Environment variable configuration

### Raspberry Pi Optimization
- Lightweight container configuration
- Resource usage optimization
- Startup and shutdown procedures
- Data persistence across reboots

## Implementation Plan

### Phase 1: Backend Foundation
1. Set up FastAPI project structure
2. Implement database models with SQLAlchemy
3. Create core API endpoints
4. Implement authentication system
5. Set up WebSocket server

### Phase 2: Device Integration
1. Create device abstraction layer
2. Implement device discovery and management
3. Develop Xiaomi device integration
4. Implement device state management
5. Create device control API

### Phase 3: Automation Engine
1. Design automation rule schema
2. Implement rule evaluation engine
3. Create background worker for triggers
4. Develop action execution system
5. Implement automation API

### Phase 4: Frontend Development
1. Set up Next.js project with ShadCN
2. Create responsive layout and navigation
3. Implement device management UI
4. Develop automation builder interface
5. Create user registration and settings

### Phase 5: Integration and Testing
1. Connect frontend to backend API
2. Implement WebSocket client for real-time updates
3. Write comprehensive tests
4. Create Docker configuration
5. Test on Raspberry Pi environment

### Phase 6: Documentation and Finalization
1. Create user documentation
2. Write developer guidelines
3. Prepare contribution terms
4. Finalize open-source license and terms
5. Package for distribution
