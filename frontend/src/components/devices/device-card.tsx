/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { Device, DeviceState, DeviceResponse } from "@/lib/devices";

interface DeviceCardProps {
  device: Device;
  deviceState: DeviceState;
  deviceResponse: DeviceResponse;
  onToggle?: (id: string, state: boolean) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function DeviceCard({ device, deviceState, deviceResponse, onToggle, onEdit, onDelete }: Readonly<DeviceCardProps>) {
  // Ensure the `power` property is handled safely
  const powerState = deviceState?.state?.power ?? "unknown"; // Default to 'unknown' if undefined
  const capabilities = deviceResponse?.properties || [];
  const [isPowered, setIsPowered] = useState(powerState === "on");

  const handleToggle = (checked: boolean) => {
    setIsPowered(checked);
    if (onToggle) {
      onToggle(device.id, checked);
    }
  };

  const getDeviceIcon = () => {
    switch (device.type) {
      case "light":
      case "bulb":
        return <LightbulbIcon className="h-5 w-5" />;
      case "switch":
      case "plug":
        return <PlugIcon className="h-5 w-5" />;
      case "thermostat":
        return <ThermostatIcon className="h-5 w-5" />;
      case "sensor":
        return <SensorIcon className="h-5 w-5" />;
      case "vacuum":
        return <VacuumIcon className="h-5 w-5" />;
      default:
        return <DeviceIcon className="h-5 w-5" />;
    }
  };

  const getStateDisplay = () => {
    const stateItems: string[] = [];
    if (["light", "bulb"].includes(device.type)) {
        if (deviceState?.state?.brightness !== undefined) {
            stateItems.push(`Brightness: ${deviceState?.state?.brightness}%`);
        }
        if (deviceState?.state?.color_temp !== undefined) {
            stateItems.push(`Color Temp: ${deviceState?.state?.color_temp}K`);
        }
    }
    if (device.type === "thermostat") {
        if (deviceState?.state?.current_temperature !== undefined) {
            stateItems.push(`Current: ${deviceState?.state?.current_temperature}°C`);
        }
        if (deviceState?.state?.target_temperature !== undefined) {
            stateItems.push(`Target: ${deviceState?.state?.target_temperature}°C`);
        }
        if (deviceState?.state?.mode !== undefined) {
            stateItems.push(`Mode: ${deviceState?.state?.mode}`);
        }
    }
    if (device.type === "sensor") {
        if (deviceState?.state?.temperature !== undefined) {
            stateItems.push(`Temp: ${deviceState?.state?.temperature}°C`);
        }
        if (deviceState?.state?.humidity !== undefined) {
            stateItems.push(`Humidity: ${deviceState?.state?.humidity}%`);
        }
        if (deviceState?.state?.motion !== undefined) {
            stateItems.push(`Motion: ${deviceState?.state?.motion ? "Detected" : "None"}`);
        }
    }
    return stateItems;
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="flex items-center">
            <div className="mr-2 p-2 bg-primary/10 rounded-full">
              {getDeviceIcon()}
            </div>
            <div>
              <CardTitle className="text-base">{device.name}</CardTitle>
              <CardDescription>
                {device.manufacturer} {device.model}
              </CardDescription>
            </div>
          </div>
          <Badge variant={deviceResponse?.status === "online" ? "default" : "outline"}>
            {deviceResponse?.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {/* Ensure `capabilities` is defined before using `.includes()` */}

          {
            capabilities.includes("on_off") && (
              <div className="flex items-center justify-between">
                <Label htmlFor={`power-${device.id}`}>Power</Label>
                <Switch
                  id={`power-${device.id}`}
                  checked={isPowered}
                  onCheckedChange={handleToggle}
                  disabled={deviceResponse?.status === "offline"}
                />
              </div>
            )}

          {getStateDisplay().map((item, index) => (
            <div key={`${device.id}-${index}`} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{item}</span>
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter className="border-t pt-3 flex justify-between">
        <Button variant="outline" size="sm" onClick={() => onEdit?.(device.id)}>
          <PencilIcon className="h-4 w-4 mr-1" />
          Edit
        </Button>
        <Button variant="outline" size="sm" onClick={() => onDelete?.(device.id)}>
          <TrashIcon className="h-4 w-4 mr-1" />
          Remove
        </Button>
      </CardFooter>
    </Card>
  );
}

function DeviceIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <line x1="8" x2="16" y1="21" y2="21" />
      <line x1="12" x2="12" y1="17" y2="21" />
    </svg>
  );
}

function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
      <path d="M9 18h6" />
      <path d="M10 22h4" />
    </svg>
  );
}

function PlugIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 22v-5" />
      <path d="M9 7V2" />
      <path d="M15 7V2" />
      <path d="M6 13V8h12v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4Z" />
    </svg>
  );
}

function ThermostatIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z" />
      <path d="M12 10v4" />
    </svg>
  );
}

function SensorIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M7 22H2V7h10" />
      <path d="M22 7v10.5c0 .83-.67 1.5-1.5 1.5s-1.5-.67-1.5-1.5V10h-8V7h11Z" />
      <path d="M7 7v10.5c0 .83-.67 1.5-1.5 1.5S4 18.33 4 17.5V7" />
      <path d="M4 7V5c0-1.1.9-2 2-2h12a2 2 0 0 1 2 2v2" />
      <path d="M11 16a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" />
    </svg>
  );
}

function VacuumIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v4" />
      <path d="M2 12h4" />
      <path d="M12 18v4" />
      <path d="M18 12h4" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
      <path d="m15 5 4 4" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  );
}
