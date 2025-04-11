'use client';

import { useState } from "react";
import { DeviceCard } from "@/components/devices/device-card";
import { DeviceForm } from "@/components/devices/device-form";
import { Button } from "@/components/ui/button";
import { MainLayout } from "@/components/layout/main-layout";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { useDevices, Device } from "@/lib/devices";

export default function DevicesPage() {
    const { devices: fetchedDevices } = useDevices();
    const [devices, setDevices] = useState<Device[]>(() => fetchedDevices.map(device => ({
        ...device,
        status: "offline", // Default status
        state: device.state || {},
        capabilities: [] // Default capabilities
    })));
    const [isAddingDevice, setIsAddingDevice] = useState(false);
    const [editingDevice, setEditingDevice] = useState<Device | null>(null);

    const handleAddDevice = (newDevice: Device) => {
        setDevices([...devices, newDevice]);
        setIsAddingDevice(false);
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
                                    key={device.id} // Ensure unique key
                                    device={device}
                                    deviceState={device.state || {}} // Provide a default empty object for deviceState
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