# Violt Core - Open-Source Smart Home Automation

## Overview

**Violt Core** is an **open-source, privacy-first smart home automation
platform** that runs locally, ensuring **full data security** without cloud
dependency. It supports **Zigbee, Z-Wave, Wi-Fi, MQTT, and Matter**, enabling
**custom automations, real-time monitoring, and API integrations** on
**self-hosted devices** like Raspberry Pi and NUC. 🚀

### **Key Features**

✅ Local execution (no cloud required)
✅ Device support for **Wi-Fi, MQTT, Zigbee, Z-Wave**
✅ Web & mobile UI for managing devices and automations
✅ Extensible API for third-party integrations
✅ Automation engine (event-driven rules-based system)
✅ Secure **end-to-end encryption**
✅ Robotics (coming soon)

## **Getting Started**

### **Prerequisites**

- Python 3.10+
- Node.js 18+
- PostgreSQL or SQLite (for local setup)
- Docker (optional for containerized deployment)
- MQTT Broker (e.g., Mosquitto)

### **Installation**

#### **1️⃣ Clone the Repository**

```sh
git clone https://github.com/yourusername/violt-core.git
cd violt-core
```

### **2️⃣ Set Up Virtual Environment (Backend)**

```sh
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### **3️⃣ Start the Backend**

```sh
uvicorn src.api.main:app --reload
```

### **4️⃣ Start the Web UI**

```sh
cd src/ui
npm install
npm run dev
```

## **API Documentation**

Violt Core provides a RESTful API for managing devices, automations, and system
configurations.

📌 Full API Documentation: Swagger Docs

## **Community & Contributions**

Violt Core is open-source and welcomes contributions! Read our Contribution
Guide for details.

### **1️⃣ License**

Licensed under Apache 2.0 – Free to use, modify, and extend.

### **2️⃣ CONTRIBUTING.md (Violt Core)**

## Contributing to Violt Core

Thank you for your interest in contributing to Violt Core! This guide outlines
the contribution process.

## **How to Contribute**

1️⃣ **Fork the Repository**

2️⃣ **Create a Feature Branch**

```sh
git checkout -b feature-new-device-support
```

3️⃣ **Make Your Changes & Run Tests**

4️⃣ **Submit a Pull Request (PR)**

### **3️⃣ Code Guidelines**

- Follow PEP 8 for Python code
- Use ESLint + Prettier for JavaScript
- Write unit tests for new functionality

### **4️⃣ Reporting Issues**

- Use the GitHub Issues tab for bug reports and feature requests.

### **5️⃣ SECURITY.md (Violt Core)**

### **Security Policy - Violt Core**

## **Security Best Practices**

- **Encryption:** All data transmissions use TLS 1.3.
- **Authentication:** API endpoints require JWT authentication.
- **Local Storage:** User data remains on-device unless explicitly synced.

## **Reporting Security Issues**

If you find a vulnerability, please **email <security@violt.app>** instead of
opening a public issue.

[Backlog](https://github.com/violt-app/violt-core/blob/main/BACKLOG.md)
