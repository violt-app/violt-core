'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useEffect, useState, useRef } from "react";
import { Device } from "@/types/device-type";
import { DeviceState } from "@/types/device-state-type";
import React from "react";
import { useError } from "@/lib/error";
import { DeviceIcon } from "../icons/device-icon";
import { PencilIcon } from "../icons/pencil-icon";
import { TrashIcon } from "../icons/trash-icon";
import { VacuumIcon } from "../icons/vacuum-icon";
import { SensorIcon } from "../icons/sensor-icon";
import { ThermostatIcon } from "../icons/thermostat-icon";
import { PlugIcon } from "../icons/plug-icon";
import { LightbulbIcon } from "../icons/lightbulb-icon";

interface DeviceCardProps {
  device: Device;
  onToggle?: (id: string, state: boolean) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onConnect?: (id: string) => void;
  onDisconnect?: (id: string) => void;
  onUpdate?: (id: string, state: DeviceState) => void;
  onRefresh?: (id: string) => void;
  onRename?: (id: string, name: string) => void;
  onReboot?: (id: string) => void;
  onFactoryReset?: (id: string) => void;
  onUpdateFirmware?: (id: string) => void;
  onUpdateSettings?: (id: string) => void;
  onUpdateConfig?: (id: string) => void;
  onUpdateNetwork?: (id: string) => void;
}

export function DeviceCard({ device, onToggle, onEdit, onDelete, onConnect, onDisconnect }: Readonly<DeviceCardProps>) {

  // Handle device state and status
  const powerState = device.state?.power ?? "unknown";

  // Track and update device status locally
  const [statusState, setStatusState] = useState<Device['status']>(device.status);

  // Local error for this device only
  const { setError, clearError, displayError } = useError();

  const capabilities = device.properties?.capabilities || [];
  const [isPowered, setIsPowered] = useState(powerState === "on");
  const [isConnecting, setIsConnecting] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync statusState to server-driven prop; clear connecting flag and errors appropriately
  useEffect(() => {
    setStatusState(device.status);
    // if not in connecting, clear local connecting flag
    if (device.status !== 'connecting') {
      setIsConnecting(false);
    }
    // clear previous errors on successful connect
    if (device.status === 'connected') {
      clearError();
    }
  }, [clearError, device.status]);

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
    const state = device.state;
    if (!state) return [];

    if (capabilities.includes("brightness") && state.brightness !== undefined) {
      stateItems.push(`Brightness: ${state.brightness}%`);
    }

    if (capabilities.includes("color_temp") && state.color_temp !== undefined) {
      stateItems.push(`Color Temp: ${state.color_temp}K`);
    }

    if (capabilities.includes("temperature") && state.temperature !== undefined) {
      stateItems.push(`Temp: ${state.temperature}°C`);
    }

    if (capabilities.includes("humidity") && state.humidity !== undefined) {
      stateItems.push(`Humidity: ${state.humidity}%`);
    }

    if (capabilities.includes("motion") && state.motion !== undefined) {
      stateItems.push(`Motion: ${state.motion ? "Detected" : "None"}`);
    }

    if (capabilities.includes("battery") && state.battery !== undefined) {
      stateItems.push(`Battery: ${state.battery}%`);
    }

    return stateItems;
  };

  const handleConnect = () => {
    clearError();
    if (!device.id) return;
    if (isConnecting) {
      // cancel connection
      if (timerRef.current) clearTimeout(timerRef.current);
      setStatusState('offline');
      setIsConnecting(false);
      onDisconnect?.(device.id);
      return;
    }
    // initiate connection
    setStatusState('connecting');
    setIsConnecting(true);
    onConnect?.(device.id);
    // timeout to revert if no server update
    timerRef.current = setTimeout(() => {
      setError('', new Error('Connection timed out'));
      setStatusState('offline');
      setIsConnecting(false);
      onDisconnect?.(device.id);
      timerRef.current = null;
    }, 10000);
  };

  // local statusState and errorMessage are per-device; cleanup handled in handleConnect

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
          <Badge
            variant={statusState === "connected" ? "default" : "outline"}
            className={
              statusState === "error"
                ? "bg-destructive text-destructive-foreground"
                : statusState === "unknown"
                  ? "bg-muted text-muted-foreground"
                  : ""
            }
          >
            {(() => {
              switch (statusState) {
                case "connected": return "Connected";
                case "connecting": return "Connecting...";
                case "offline": return "Offline";
                case "error": return "Error";
                case "unknown": return "Unknown";
                default: return statusState;
              }
            })()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {/* Ensure `capabilities` is defined before using `.includes()` */}

          {
            capabilities.includes("power") && (
              <div className="flex items-center justify-between">
                <Label htmlFor={`power-${device.id}`}>Power</Label>
                <Switch
                  id={`power-${device.id}`}
                  checked={isPowered}
                  onCheckedChange={handleToggle}
                  disabled={statusState !== "connected"}
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
      <CardFooter className="flex justify-between pt-2">
        <div className="flex gap-2">
          {/* Existing edit and delete buttons */}
          {onEdit && (
            <Button variant="ghost" size="icon" onClick={() => onEdit(device.id)}>
              <PencilIcon className="h-4 w-4" />
            </Button>
          )}
          {onDelete && (
            <Button variant="ghost" size="icon" onClick={() => onDelete(device.id)}>
              <TrashIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="inline-flex items-center gap-4">
          {/* Connect button for offline, connecting, or unknown */}
          {(statusState === 'offline' || statusState === 'connecting' || statusState === 'unknown') && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleConnect}
            >
              {isConnecting && <span className="animate-spin mr-2">⭮</span>}
              {isConnecting ? 'Cancel Connection' : 'Connect'}
            </Button>
          )}

          {/* Existing power toggle */}
          {capabilities.includes('power') && (
            <div className="flex items-center space-x-2">
              <Label htmlFor={`power-${device.id}`}>Power</Label>
              <Switch
                id={`power-${device.id}`}
                checked={isPowered}
                onCheckedChange={handleToggle}
              />
            </div>
          )}
        </div>
      </CardFooter>
      {
        <div className="pt-4 pl-4 text-destructive">
          {displayError()}
        </div>
      }
    </Card>
  );
}