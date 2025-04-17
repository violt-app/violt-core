/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect } from "react";
import { DeviceCard } from "@/components/devices/device-card";
import { DeviceForm } from "@/components/devices/device-form";
import { Button } from "@/components/ui/button";
import { MainLayout } from "@/components/layout/main-layout";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { useDevices } from "@/lib/devices";
import { Device } from "@/types/device-type";
import { useError } from "@/lib/error";

export default function DevicesPage() {
    const { devices: fetchedDevices, fetchDevices, addDevice, connectDevice } = useDevices();
    const { setError } = useError();
    const [devices, setDevices] = useState<Device[]>([]);

    useEffect(() => {
        fetchDevices(); // Fetch devices when the page loads
    }, [fetchDevices]);

    useEffect(() => {
        setDevices(fetchedDevices.map(device => ({
            name: device.name || '',
            type: device.type || '',
            manufacturer: device.manufacturer || '',
            integration_type: device.integration_type || '',
            id: device.id,
            model: device.model,
            location: device.location,
            ip_address: device.ip_address,
            mac_address: device.mac_address,
            status: (device.status || "offline") as "connected" | "offline" | "error" | "connecting",
            state: device.state || {},
            properties: {
                capabilities: device.properties?.capabilities || [],
                supported_features: device.properties?.supported_features || []
            },
            created_at: device.created_at,
            last_updated: device.last_updated,
            config: device.config
        })));
    }, [fetchedDevices]);

    const [isAddingDevice, setIsAddingDevice] = useState(false);
    const [editingDevice, setEditingDevice] = useState<Device | null>(null);

    const handleAddDevice = (newDevice: Device) => {
        addDevice(newDevice).then((addedDevice) => {
            setDevices((prev) => [...prev, addedDevice]);
            setIsAddingDevice(false);
        });
    };

    const handleEditDevice = (updatedDevice: Device) => {
        setDevices(devices.map((device) =>
            device.id === updatedDevice.id ? updatedDevice : device
        ));
        setEditingDevice(null);
    };

    const handleDeleteDevice = (id: string) => {
        setDevices((prev) => prev.filter((device) => device.id !== id));
    };

    const handleConnectDevice = async (id: string) => {
        let result = await connectDevice(id);
        setError(result.detail);
    }

    return (
        <MainLayout
            sidebar={<Sidebar />}
            header={<Header title="Devices" subtitle="Manage your smart devices" />}
        >
            <div className="p-4">
                {isAddingDevice && (
                    <DeviceForm
                        onSubmit={handleAddDevice}
                        onCancel={() => setIsAddingDevice(false)}
                    />
                )}

                {editingDevice && (
                    <DeviceForm
                        device={{ ...editingDevice, model: editingDevice?.model ?? "" }}
                        onSubmit={handleEditDevice}
                        onCancel={() => setEditingDevice(null)}
                    />
                )}

                {!isAddingDevice && !editingDevice && (
                    <div>
                        <Button onClick={() => setIsAddingDevice(true)}>Add Device</Button>
                        <div className="grid gap-4 mt-4">
                            {devices.map((device) => (
                                <DeviceCard
                                    key={device.id}
                                    device={{
                                        ...device,
                                        status: device.status as "connected" | "offline" | "error" | "connecting",
                                        state: device.state || {},
                                        properties: {
                                            capabilities: device.properties?.capabilities || [],
                                            supported_features: device.properties?.supported_features || []
                                        }
                                    }}
                                    onEdit={(id) =>
                                        setEditingDevice(devices.find((d) => d.id === id) || null)
                                    }
                                    onDelete={handleDeleteDevice}
                                    onConnect={handleConnectDevice}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}