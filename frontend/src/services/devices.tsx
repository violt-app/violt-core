/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { DeviceInput } from "@/types/device-input-type";
import { DeviceResponse } from "@/types/device-response-type";
import { Device } from "@/types/device-type";
import { createContext, useContext, useState, useEffect, ReactNode, useMemo, useCallback } from "react";
import { useError } from "./error";

interface DeviceContextType {
  devices: DeviceResponse[];
  isLoading: boolean;
  fetchDevices: () => Promise<void>;
  getDevice: (id: string) => DeviceResponse | undefined;
  addDevice: (device: DeviceInput) => Promise<Device>;
  updateDevice: (id: string, device: DeviceInput) => Promise<Device>;
  deleteDevice: (id: string) => Promise<void>;
  toggleDevicePower: (id: string, state: boolean) => Promise<void>;
  executeDeviceCommand: (id: string, command: string, params?: Record<string, any>) => Promise<void>;
  discoverDevices: () => Promise<string[]>;
  connectDevice: (deviceId: string) => Promise<any>;
  // Add any other methods you need
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

interface DeviceProviderProps {
  readonly children: ReactNode;
}

export function DeviceProvider({ children }: DeviceProviderProps) {
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { setError, clearError } = useError();

  const fetchDevices = useCallback(async () => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        setError("Authentication required");
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/devices/all", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      let responseData;
      try {
        responseData = await response.json();
      } catch (error) {
        console.error("Failed to parse JSON response:", error);
        throw new Error("Failed to parse JSON response");
      }

      if (!response.ok) {
        console.error("Failed to fetch devices:", responseData.detail);
        setError(responseData.detail);
        throw new Error("Failed to fetch devices");
      }

      setDevices(responseData);
    } catch (error) {
      console.error("Error fetching devices:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError]);

  const getDevice = useCallback((id: string) => {
    return devices.find(device => device.id === id);
  }, [devices]);

  const addDevice = useCallback(async (device: DeviceInput): Promise<Device> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        setError("Authentication required");
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/devices/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(device),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message ?? "Failed to add device");
      }

      const newDevice = await response.json();
      console.log("New device added:", newDevice);
      setDevices(prev => [...prev, newDevice]);
      return newDevice;
    } catch (error) {
      console.error("Error adding device:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError]);

  const updateDevice = useCallback(async (id: string, device: DeviceInput): Promise<Device> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/devices/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(device),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message ?? "Failed to update device");
      }

      const updatedDevice = await response.json();
      setDevices(prev => prev.map(d => d.id === id ? updatedDevice : d));
      return updatedDevice;
    } catch (error) {
      console.error("Error updating device:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError]);

  const deleteDevice = useCallback(async (id: string): Promise<void> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/devices/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message ?? "Failed to delete device");
      }

      setDevices(prev => prev.filter(d => d.id !== id));
    } catch (error) {
      console.error("Error deleting device:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError]);

  const executeDeviceCommand = useCallback(async (id: string, command: string, params: Record<string, any> = {}): Promise<void> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/devices/${id}/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          command,
          params
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to execute command");
      }

      // Fetch updated device state
      await fetchDevices();
    } catch (error) {
      console.error("Error executing device command:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [fetchDevices, clearError, setError]);

  const toggleDevicePower = useCallback(async (id: string, state: boolean): Promise<void> => {
    clearError();

    try {
      const command = state ? "turn_on" : "turn_off";
      await executeDeviceCommand(id, command);

      // Update local state optimistically
      setDevices(prev => prev.map(d => {
        if (d.id === id) {
          return {
            ...d,
            state: {
              ...d.state,
              state: d.state || {}, // Ensure state is defined
              power: state ? "on" : "off"
            }
          };
        }
        return d;
      }));
    } catch (error) {
      console.error("Error toggling device power:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      // Re-throw the error after logging, or handle it appropriately
      throw error;
    }
  }, [executeDeviceCommand, clearError, setError]); // Add executeDeviceCommand as a dependency

  const discoverDevices = useCallback(async (): Promise<string[]> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/devices/discover`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const devices = data.discovered_devices ?? [];
      return devices.map((device: any) => device.name);
    } catch (error) {
      console.error("Error scanning for devices:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError]);

  const connectDevice = useCallback(async (deviceId: string): Promise<any> => {
    setIsLoading(true);
    clearError();
    let responseData: any;

    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        setError("Authentication required");
        throw new Error("Authentication required");
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/devices/${deviceId}/connect`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );


      try {
        responseData = await response.json();
      }
      catch (error) {
        console.error("Failed to parse JSON response:", error);
        console.log("Response text:", responseData.detail);
        throw new Error("Failed to parse JSON response");
      }

      if (!response.ok) {
        // Propagate backend error to caller for per-device handling
        throw new Error(responseData.detail || 'Failed to connect device');
      }

      // Refresh devices list so statuses are up-to-date
      await fetchDevices();
      return responseData;
    }
    catch (error) {
      console.error("Error connecting to device:", responseData.detail);
      setError(responseData.detail);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, setError, fetchDevices]);

  useEffect(() => {
    // Fetch devices on initial load if user is authenticated
    const token = localStorage.getItem("authToken");
    if (token) {
      fetchDevices();
    }
  }, [fetchDevices]);

  const contextValue = useMemo(() => ({
    devices,
    isLoading,
    fetchDevices,
    getDevice,
    addDevice,
    updateDevice,
    deleteDevice,
    toggleDevicePower,
    executeDeviceCommand,
    discoverDevices,
    connectDevice,
  }), [devices,
    isLoading,
    fetchDevices,
    getDevice,
    addDevice,
    updateDevice,
    deleteDevice,
    toggleDevicePower,
    executeDeviceCommand,
    discoverDevices,
    connectDevice]);

  return (
    <DeviceContext.Provider value={contextValue}>
      {children}
    </DeviceContext.Provider>
  );
}

export function useDevices() {
  const context = useContext(DeviceContext);

  if (context === undefined) {
    throw new Error("useDevices must be used within a DeviceProvider");
  }

  return context;
}
