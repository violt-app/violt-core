export interface DeviceInput {
    name: string;
    type: string;
    manufacturer: string;
    model?: string;
    integration_type: string;
    ip_address?: string;
    mac_address?: string;
}