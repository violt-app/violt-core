import { DeviceState } from "./device-state-type";

export enum DeviceStatus {
    CONNECTED = "connected",
    OFFLINE = "offline",
    ERROR = "error",
    CONNECTING = "connecting",
    UNKNOWN = "unknown"
}

export enum DeviceCapability {
    POWER = "power",
    BRIGHTNESS = "brightness",
    COLOR = "color",
    COLOR_TEMP = "color_temp",
    TEMPERATURE = "temperature",
    HUMIDITY = "humidity",
    MOTION = "motion",
    BATTERY = "battery"
}

export interface DeviceProperties {
    capabilities: string[];
    supported_features: string[];
}

export interface Device {
    id: string;
    name: string;
    type: string;
    manufacturer: string;
    model?: string;
    location?: string;
    ip_address?: string;
    mac_address?: string;
    integration_type: string;
    status: "connected" | "offline" | "error" | "connecting" | "unknown";
    properties: DeviceProperties;
    state: DeviceState;
    created_at?: Date;
    last_updated?: Date;
    config?: {
        token?: string;
        username?: string;
        password?: string;
        host?: string;
        port?: number;
    };
}