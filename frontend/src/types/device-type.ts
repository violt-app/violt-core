import { DeviceState } from "./device-state-type";

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
    state?: DeviceState;
}