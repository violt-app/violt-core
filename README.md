# Violt Core Lite MVP

**Violt Core Lite** is the open-source foundation of the Violt Smart Home Automation platform. This local-first MVP offers private, offline control of smart home devices with future extensibility for AI integration.

## 🚀 Key Features

- Fully offline smart home engine
- Supports Zigbee, Z-Wave, Wi-Fi, MQTT, Matter
- YAML/JSON-based rule engine
- REST & MQTT APIs
- Docker-ready for edge devices (Raspberry Pi, NUC)

## 📦 Project Structure

```md
└── 📁violt-core
    └── 📁.github
    └── 📁config
    └── 📁docs
        └── SECURITY.md
    └── 📁scripts
    └── 📁src
        └── 📁api
        └── 📁automation
        └── 📁database
        └── 📁devices
        └── 📁mobile
        └── 📁security
        └── 📁tests
        └── 📁ui
    └── .gitignore
    └── BACKLOG.md
    └── LICENSE
    └── README.md
```

## 🛠️ Getting Started

1. Clone the repo  
   `git clone https://github.com/yourusername/violt-core-lite.git`
2. Install dependencies  
   `npm install` or `pip install -r requirements.txt` (based on stack)
3. Run locally  
   `npm run dev` or `python main.py`

## 🔒 License

This project is licensed under the **GNU AGPL v3**. See `LICENSE` for details.

## 🧠 About Violt

Violt is an AI-powered smart home automation platform offering privacy-first local control (Violt Core) with optional AI automation via the Violt AI cloud.
