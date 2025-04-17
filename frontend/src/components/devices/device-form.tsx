/* eslint-disable @typescript-eslint/no-explicit-any */

'use client';

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDevices } from "@/lib/devices";
import { useError } from "@/lib/error";

interface DeviceFormProps {
  readonly device?: {
    readonly id?: string;
    readonly name: string;
    readonly type: string;
    readonly manufacturer: string;
    readonly model: string;
    readonly ip_address?: string;
    readonly mac_address?: string;
    readonly integration_type: string;
    readonly properties?: {
      readonly capabilities: string[];
      readonly supported_features: string[];
    };
    readonly config?: {
      readonly token?: string;
      readonly username?: string;
      readonly password?: string;
      readonly host?: string;
      readonly port?: number;
    };
  };
  readonly onSubmit: (device: any) => void;
  readonly onCancel: () => void;
  readonly isLoading?: boolean;
}

// Added a field for the config dictionary to align with the backend schema.

export function DeviceForm({ device, onSubmit, onCancel, isLoading = false }: DeviceFormProps) {
  const [formData, setFormData] = useState({
    name: device?.name ?? "",
    type: device?.type ?? "light",
    manufacturer: device?.manufacturer ?? "",
    model: device?.model ?? "",
    ip_address: device?.ip_address ?? "",
    mac_address: device?.mac_address ?? "",
    integration_type: device?.integration_type ?? "xiaomi",
    properties: device?.properties ?? {
      capabilities: [],
      supported_features: [],
    },
    config: device?.config ?? {},
  });
  const { errorMessage, displayError, clearError } = useError();
  const [activeTab, setActiveTab] = useState("manual");
  const [isScanning, setIsScanning] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState<string[]>([]);
  const { discoverDevices } = useDevices();

  // Prevent multiple calls to displayError by using useEffect
  useEffect(() => {
    if (errorMessage) {
      displayError();
    }
  }, [errorMessage, displayError]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      config: {
        ...prev.config,
        [name]: value,
      },
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    clearError();
    e.preventDefault();
    onSubmit({
      ...formData,
      id: device?.id,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>{device?.id ? "Edit Device" : "Add New Device"}</CardTitle>
          <CardDescription>
            {device?.id
              ? "Update the details of your existing device"
              : "Configure a new device to add to your smart home"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="manual">Manual Setup</TabsTrigger>
              <TabsTrigger value="discovery">Auto Discovery</TabsTrigger>
            </TabsList>
            <TabsContent value="manual" className="pt-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Device Name</Label>
                  <Input
                    id="name"
                    name="name"
                    placeholder="Living Room Light"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="type">Device Type</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(value) => handleSelectChange("type", value)}
                  >
                    <SelectTrigger id="type">
                      <SelectValue placeholder="Select device type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="switch">Switch</SelectItem>
                      <SelectItem value="sensor">Sensor</SelectItem>
                      <SelectItem value="thermostat">Thermostat</SelectItem>
                      <SelectItem value="vacuum">Vacuum Cleaner</SelectItem>
                      <SelectItem value="speaker">Smart Speaker</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="integration_type">Integration</Label>
                  <Select
                    value={formData.integration_type}
                    onValueChange={(value) => handleSelectChange("integration_type", value)}
                  >
                    <SelectTrigger id="integration_type">
                      <SelectValue placeholder="Select integration" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="xiaomi">Xiaomi</SelectItem>
                      <SelectItem value="alexa">Amazon Alexa</SelectItem>
                      <SelectItem value="google_home">Google Home</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="manufacturer">Manufacturer</Label>
                  <Input
                    id="manufacturer"
                    name="manufacturer"
                    placeholder="Xiaomi"
                    value={formData.manufacturer}
                    onChange={handleChange}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="model">Model</Label>
                  <Input
                    id="model"
                    name="model"
                    placeholder="Yeelight LED Bulb"
                    value={formData.model}
                    onChange={handleChange}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="ip_address">IP Address</Label>
                  <Input
                    id="ip_address"
                    name="ip_address"
                    placeholder="192.168.1.100"
                    value={formData.ip_address}
                    onChange={handleChange}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="mac_address">MAC Address</Label>
                  <Input
                    id="mac_address"
                    name="mac_address"
                    placeholder="00:11:22:33:44:55"
                    value={formData.mac_address}
                    onChange={handleChange}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="config-token">Device Token</Label>
                  <Input
                    id="config-token"
                    name="token"
                    placeholder="Enter device token"
                    value={formData.config.token ?? ""}
                    onChange={handleConfigChange}
                  />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="discovery" className="pt-4">
              <div className="flex flex-col items-center justify-center py-8">
                <div className="mb-4 p-4 rounded-full bg-primary/10">
                  <SearchIcon className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-lg font-medium mb-2">Discover Devices</h3>
                <p className="text-center text-muted-foreground mb-4">
                  Violt will scan your network for compatible smart devices
                </p>
                <Button type="button" className="mb-4" onClick={async () => {
                  setIsScanning(true);
                  setDiscoveredDevices([]);

                  try {
                    console.log("Scanning for devices...");
                    const devices = await discoverDevices();
                    console.log("Discovered devices:", devices);
                    setDiscoveredDevices(devices);
                  } catch (error) {
                    console.error("Error scanning for devices:", error);
                  } finally {
                    setIsScanning(false);
                  }
                }} disabled={isScanning}>
                  {isScanning ? "Scanning..." : "Start Scanning"}
                </Button>
                {discoveredDevices.length > 0 ? (
                  <ul className="w-full border rounded-md p-4 text-center">
                    {discoveredDevices.map((device) => (
                      <li key={device} className="text-muted-foreground">
                        {device}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="w-full border rounded-md p-4 text-center text-muted-foreground">
                    {isScanning
                      ? "Scanning for devices..."
                      : "No devices found. Make sure your devices are powered on and connected to the same network."}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
          {errorMessage && (
            <div className="text-red-500 text-sm">{errorMessage}</div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" type="button" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading && (
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800"></div>
            )}
            {device?.id ? "Update Device" : "Add Device"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}

function SearchIcon({ className }: { readonly className?: string }) {
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
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}