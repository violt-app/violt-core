/* eslint-disable @typescript-eslint/no-explicit-any */

export interface DeviceState {
    power?: 'on' | 'off';
    brightness?: number;
    color_temp?: number;
    color?: string;
    temperature?: number;
    humidity?: number;
    motion?: boolean;
    battery?: number;
}