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

export default function DevicesPage() {
    const { devices: fetchedDevices, fetchDevices, addDevice } = useDevices(); // Add fetchDevices to fetch devices explicitly
    const [devices, setDevices] = useState<Device[]>([]);

    useEffect(() => {
        fetchDevices(); // Fetch devices when the page loads
    }, [fetchDevices]);

    useEffect(() => {
        setDevices(fetchedDevices.map(device => ({
            name: '',
            type: '',
            manufacturer: '',
            integration_type: '',
            ...device,
            status: "offline",
            state: device.state || { state: {} },
            capabilities: []
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
                                    device={device}
                                    deviceState={device.state || { state: {} }} // Provide a default DeviceState object
                                    deviceResponse={{
                                        id: device.id,
                                        status: (device as any).status ?? "unknown", // Cast to 'any' to bypass type error or update the Device type definition
                                        state: device.state || { state: {} },
                                        created_at: new Date(), // Use Date object directly
                                        last_updated: new Date(), // Use Date object directly
                                    }} // Provide a default or actual DeviceResponse object
                                    onEdit={(id) =>
                                        setEditingDevice(devices.find((d) => d.id === id) || null)
                                    }
                                    onDelete={handleDeleteDevice}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}