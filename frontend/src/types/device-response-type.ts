/* eslint-disable @typescript-eslint/no-explicit-any */
import { DeviceState } from "./device-state-type";

export interface DeviceResponse {
    id: string;
    name: string;
    type: string;
    manufacturer: string;
    model?: string;
    location?: string;
    ip_address?: string;
    mac_address?: string;
    integration_type: string;
    status: "connected" | "offline" | "error" | "connecting";
    properties?: {
        capabilities: string[];
        supported_features: string[];
    };
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