/* eslint-disable @typescript-eslint/no-explicit-any */
import { DeviceState } from "./device-state-type";

export interface DeviceResponse {
    id: string;
    status: string;
    properties?: Record<string, any>;
    state: DeviceState;
    created_at: Date;
    last_updated: Date;
}