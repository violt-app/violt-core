'use client';

import { useState, useEffect } from "react";
import { DeviceCard } from "@/components/devices/device-card";
import { DeviceForm } from "@/components/devices/device-form";
import { Button } from "@/components/ui/button";
import { MainLayout } from "@/components/layout/main-layout";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { useDevices } from "@/services/devices";
import { Device } from "@/types/device-type";
import { useError } from "@/services/error";
import { useWebSocket } from "@/services/websocket";

export default function DevicesPage() {
    // Only use implemented context methods
    const { fetchDevices, addDevice, updateDevice, deleteDevice, connectDevice, devices } = useDevices();
    const { clearError } = useError();
    const { lastMessage } = useWebSocket();

    // Remove local devices state
    // const [devices, setDevices] = useState<Device[]>([]);

    const [isAddingDevice, setIsAddingDevice] = useState(false);
    const [isDeletingDevice, setIsDeletingDevice] = useState(false);
    const [deletingDeviceId, setDeletingDeviceId] = useState<string | null>(null);
    const [editingDevice, setEditingDevice] = useState<Device | null>(null);
    // Prepare BLE/Hub logic for when backend endpoints are ready
    // const [isAddingBLEDevice, setIsAddingBLEDevice] = useState(false);
    // const [isAddingHub, setIsAddingHub] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("authToken");
        if (token) {
            fetchDevices();
        }
    }, [fetchDevices]);

    useEffect(() => {

    }, [lastMessage]);

    // Effect: If deletingDeviceId is set, and that device is no longer in the devices list, clear deleting state
    useEffect(() => {
        if (isDeletingDevice && deletingDeviceId) {
            const stillExists = devices.some(d => d.id === deletingDeviceId);
            if (!stillExists) {
                setIsDeletingDevice(false);
                setDeletingDeviceId(null);
            }
        }
    }, [devices, isDeletingDevice, deletingDeviceId]);

    const handleAddDevice = (newDevice: Device) => {
        addDevice(newDevice).then(() => {
            setIsAddingDevice(false);
        });
    };

    const handleEditDevice = (updatedDevice: Device) => {
        clearError();
        setEditingDevice(updatedDevice);

        updateDevice(updatedDevice.id, updatedDevice).then(() => {
            // No need to update local state, context will update devices
        }).catch(() => {
            // Handle error if needed
        }).finally(() => {
            setEditingDevice(null);
        });
    };

    const handleDeleteDevice = (id: string) => {
        setIsDeletingDevice(true);
        setDeletingDeviceId(id);
        deleteDevice(id).then(() => {
            if (lastMessage?.type === 'device_removed') {
                // Remove the device from your state/UI
                setIsDeletingDevice(false);
                setDeletingDeviceId(null);
            }
        });
    };

    const handleConnectDevice = async (id: string) => {
        clearError();
        try {
            await connectDevice(id);
        } catch {
            // connectDevice sets error and triggers fetchDevices if applicable
        }
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

                {isDeletingDevice && (
                    <div className="text-red-500">Deleting device...</div>
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
                                    onEdit={(id) => {
                                        const found = devices.find((d) => d.id === id);
                                        setEditingDevice(
                                            found
                                                ? {
                                                    ...found,
                                                    properties: {
                                                        capabilities: found.properties?.capabilities || [],
                                                        supported_features: found.properties?.supported_features || []
                                                    }
                                                }
                                                : null
                                        );
                                    }}
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